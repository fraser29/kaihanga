import argparse
import sys
import os

from ngawari import fIO, vtkfilters
import vtk



# =============================================================================================
def _read_stl(input_path):
    return fIO.readVTKFile(input_path)

def _write_stl(output_path, stlObj, input_path, abbrev):
    if (output_path is None) or os.path.isdir(output_path):
        fName_in = os.path.split(input_path)[1]
        fExt = os.path.splitext(fName_in)[1]
        fName = f"{fName_in}_{abbrev}.{fExt}"
        if output_path is None:
            output_path = os.path.join(os.path.dirname(input_path), fName)
        else:
            output_path = os.path.join(output_path, fName)
    fIO.writeVTKFile(stlObj, output_path)   


def decimate_model(input_path, output_path, decimate_value):
    stlObj = _read_stl(input_path)
    stlObj = vtkfilters.decimateTris(stlObj, decimate_value)
    _write_stl(output_path, stlObj, input_path, "decimate")


def model_to_wireframe(input_path, output_path):
    stlObj = _read_stl(input_path)
    edges = vtkfilters.filterExtractEdges(stlObj)
    nCells = edges.GetNumberOfCells()
    lines, norms = [], []
    

    _write_stl(output_path, edges, input_path, "wireframe")


def create_edge_boxes(input_path, output_path, box_width):
    """Create boxes along edges with orientation based on adjacent face normals."""
    stlObj = _read_stl(input_path)
    
    # Create edge extraction filter
    edge_filter = vtk.vtkFeatureEdges()
    edge_filter.SetInputData(stlObj)
    edge_filter.BoundaryEdgesOn()
    edge_filter.FeatureEdgesOn()
    edge_filter.ManifoldEdgesOff()
    edge_filter.NonManifoldEdgesOff()
    edge_filter.Update()
    edges = edge_filter.GetOutput()

    # Create append filter to combine all boxes
    append_filter = vtk.vtkAppendPolyData()
    
    # Get cell data from original mesh
    cell_normals = vtk.vtkPolyDataNormals()
    cell_normals.SetInputData(stlObj)
    cell_normals.ComputePointNormalsOff()
    cell_normals.ComputeCellNormalsOn()
    cell_normals.Update()
    mesh_with_normals = cell_normals.GetOutput()

    # For each edge
    for i in range(edges.GetNumberOfCells()):
        edge = edges.GetCell(i)
        points = edge.GetPoints()
        p1 = points.GetPoint(0)
        p2 = points.GetPoint(1)
        
        # Find connected faces and their normals
        point_id1 = edges.GetPointData().GetArray(0).GetTuple1(edge.GetPointId(0))
        point_id2 = edges.GetPointData().GetArray(0).GetTuple1(edge.GetPointId(1))
        
        # Get cells connected to these points in original mesh
        cell_ids = vtk.vtkIdList()
        stlObj.GetPointCells(int(point_id1), cell_ids)
        
        # Calculate average normal of connected faces
        avg_normal = [0.0, 0.0, 0.0]
        for j in range(cell_ids.GetNumberOfIds()):
            cell_id = cell_ids.GetId(j)
            normal = mesh_with_normals.GetCellData().GetNormals().GetTuple3(cell_id)
            avg_normal[0] += normal[0]
            avg_normal[1] += normal[1]
            avg_normal[2] += normal[2]
        
        # Normalize
        magnitude = (avg_normal[0]**2 + avg_normal[1]**2 + avg_normal[2]**2)**0.5
        if magnitude > 0:
            avg_normal = [n/magnitude for n in avg_normal]
        else:
            avg_normal = [0, 0, 1]  # default if no valid normal found

        # Create box
        edge_vector = [p2[i] - p1[i] for i in range(3)]
        edge_length = sum(v**2 for v in edge_vector)**0.5
        
        # Create transform for box orientation
        transform = vtk.vtkTransform()
        transform.PostMultiply()
        
        # Move to edge start point
        transform.Translate(p1)
        
        # Calculate rotation to align box with edge
        z_axis = [0, 0, 1]
        rotation_axis = [
            edge_vector[1]*z_axis[2] - edge_vector[2]*z_axis[1],
            edge_vector[2]*z_axis[0] - edge_vector[0]*z_axis[2],
            edge_vector[0]*z_axis[1] - edge_vector[1]*z_axis[0]
        ]
        angle = vtk.vtkMath.DegreesFromRadians(
            vtk.vtkMath.AngleBetweenVectors(edge_vector, z_axis))
        
        if sum(x*x for x in rotation_axis) > 0:
            transform.RotateWXYZ(angle, rotation_axis)
        
        # Create the box
        box = vtk.vtkCubeSource()
        box.SetXLength(box_width)
        box.SetYLength(box_width)
        box.SetZLength(edge_length)
        box.SetCenter(0, 0, edge_length/2)
        box.Update()
        
        # Apply transform
        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetInputData(box.GetOutput())
        transform_filter.SetTransform(transform)
        transform_filter.Update()
        
        # Add to append filter
        append_filter.AddInputData(transform_filter.GetOutput())
    
    append_filter.Update()
    _write_stl(output_path, append_filter.GetOutput(), input_path, "edge_boxes")


def validate_input_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    if not os.path.isfile(file_path):
        raise ValueError(f"Input file must be a file, got: {file_path}")
    if not os.path.splitext(file_path)[1].lower() == '.stl':
        raise ValueError(f"Input file must be an STL file, got: {file_path}")
    return file_path

# =============================================================================================
# =============================================================================================
def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Convert 3D STL models to wireframe with different processing options'
    )
    
    # Required argument for input STL file
    parser.add_argument(
        '-i', '--input',
        type=str,
        required=True,
        help='Path to input STL file'
    )
    
    # Optional output path
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Path to output file (default: input_[action-abbreviation].stl)'
    )
    
    # Processing options group
    processing_group = parser.add_mutually_exclusive_group(required=True)
    processing_group.add_argument(
        '--decimate',
        action='store_true',
        help='Decimate the model'
    )
    processing_group.add_argument(
        '--wireframe',
        action='store_true',
        help='Generate a wireframe'
    )
    processing_group.add_argument(
        '--decimate_value',
        type=float,
        help='Target fraction of triangles to decimate the model to (0.0 to 1.0)'
    )
    processing_group.add_argument(
        '--edge-boxes',
        type=float,
        help='Generate boxes along edges with specified width'
    )
    
    return parser.parse_args()


# =============================================================================================
# =============================================================================================
def main():
    try:
        args = parse_arguments()
        
        # Validate input file
        input_path = validate_input_file(args.input)
        
        # Generate output path if not specified
        if args.output is None:
            output_path = input_path.with_name(f"{input_path.stem}_wireframe{input_path.suffix}")
        else:
            output_path = os.path.abspath(args.output)
        
        # Process based on selected method
        if args.decimate:
            decimate_model(input_path, output_path, args.decimate_value)
        elif args.wireframe:
            model_to_wireframe(input_path, output_path)
        elif args.edge_boxes is not None:
            create_edge_boxes(input_path, output_path, args.edge_boxes)
            
        print(f"Processing complete. Output saved to: {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


# =============================================================================================
# =============================================================================================
if __name__ == "__main__":
    main()
