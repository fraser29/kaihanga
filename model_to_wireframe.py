import argparse
import sys
import os

from ngawari import fIO, vtkfilters



# =============================================================================================
def _read_stl(input_path):
    return fIO.readVtk(input_path)

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


def process_model_decimate(input_path, output_path, decimate_value):
    stlObj = _read_stl(input_path)
    stlObj = vtkfilters.decimateTris(stlObj, decimate_value)
    _write_stl(output_path, stlObj, input_path, "decimate")


def process_model_wireframe(input_path, output_path):
    stlObj = _read_stl(input_path)
    stlObj = vtkfilters.filterExtractSurface(stlObj)
    _write_stl(output_path, stlObj, input_path, "wireframe")


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
            output_path = Path(args.output)
        
        # Process based on selected method
        if args.runA:
            process_model_A(input_path, output_path)
        elif args.runB:
            process_model_B(input_path, output_path)
        elif args.runC:
            process_model_C(input_path, output_path)
            
        print(f"Processing complete. Output saved to: {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


# =============================================================================================
# =============================================================================================
if __name__ == "__main__":
    main()
