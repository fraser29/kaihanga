#!/usr/env python

# use conda env sci / uidev
import vtk
from vtk.util import numpy_support
import numpy as np
import sys
import argparse



def image_to_3D(imageFile, outputSTL=None, length_mm=0, thickness=3,
                 INVERT=False, BRACKET=False, IMAGE=False):
    if outputSTL is None:
        outputSTL = imageFile[:-4]+'.stl'
    NThick = 7

    aName = 'PNGImage'
    if imageFile.endswith('jpg'):
        aName = 'JPEGImage'
        imreader = vtk.vtkJPEGReader()
    else:
        imreader = vtk.vtkPNGReader()
    imreader.SetFileName(imageFile)
    imreader.Update()
    ii = imreader.GetOutput()
    dims = ii.GetDimensions()
    print('Input dimensions are: ', str(dims), ' spacing: ', str(ii.GetSpacing()))

    irs = vtk.vtkImageResize()
    irs.SetInputData(ii)
    irs.SetOutputDimensions(dims[0], dims[1], NThick)
    irs.Update()
    ii = irs.GetOutput()

    length_now = dims[0]-1 * 1.0
    factor = 1.0
    if length_mm > 0:
        factor = length_mm / length_now
        print('Scaling by factor of %5.2f'%(factor))  
    
    ii.SetSpacing(factor, factor ,thickness / float(NThick))
    print('Resized to dimensions: ', str(ii.GetDimensions()), ' spacing: ', str(ii.GetSpacing()))
    #    print(ii)

    A = numpy_support.vtk_to_numpy(ii.GetPointData().GetArray(aName)).copy()
    A = A[:,0].astype(float) # RGBA to Gray
    A = A / np.max(A)
    if INVERT:
        A = np.abs(A - 1.0)

    # A[A==0] = 200
    # A[A==255] = 0
    A = A - 1
    print(A.shape, np.prod(ii.GetDimensions()))
    A = np.reshape(A, ii.GetDimensions(), 'F')
    print(A.shape, np.min(A), np.max(A))
    A[:,:,0] = 0
    A[:,:,-1] = 0
    if INVERT:
        A[:, 0, :] = 0
        A[:, -1, :] = 0
        A[0, :, :] = 0
        A[-1, :, :] = 0

    npArray = np.reshape(A, np.prod(ii.GetDimensions()), 'F')
    aArray = numpy_support.numpy_to_vtk(npArray, deep=1)
    aArray.SetName('ImageScalars')
    ii.GetPointData().SetScalars(aArray)

    cf = vtk.vtkContourFilter()
    cf.SetInputData(ii)
    cf.SetValue(0, -0.5)
    cf.Update()
    triFilter = vtk.vtkTriangleFilter()
    triFilter.SetInputData(cf.GetOutput())
    triFilter.Update()
    dF = vtk.vtkDecimatePro()
    dF.SetInputData(triFilter.GetOutput())
    dF.SetTargetReduction(0.5)
    dF.Update()
    # tris = triFilter.GetOutput()
    # im2pd = vtk.vtkImageDataGeometryFilter()
    # im2pd.SetInputConnection(imreader.GetOutputPort())
    # im2pd.Update()
    # pd = im2pd.GetOutput()
    # print(imreader.GetOutput())

    ## SCALE
    output = dF.GetOutput()
    # bb = output.GetBounds()
    # length_now = bb[1] - bb[0]
    # if length_mm > 0:
    #     factor = length_mm / length_now
    #     print('Scaling by factor of %5.2f'%(factor))    
    # factor = 1

    # transP = vtk.vtkTransform()
    # transP.Scale(factor, factor, thickness / NThick)
    # tpd = vtk.vtkTransformPolyDataFilter()
    # tpd.SetInputData(dF.GetOutput())
    # tpd.SetTransform(transP)
    # tpd.Update()
    # output = tpd.GetOutput()

    print('Result bounds: ', str(output.GetBounds()))

    writer = vtk.vtkSTLWriter()
    writer.SetFileName(outputSTL)
    writer.SetInputData(output)
    writer.Write()
    if IMAGE:
        outputVTI = imageFile[:-4]+'.vti'
        writer = vtk.vtkXMLImageDataWriter()
        writer.SetFileName(outputVTI)
        writer.SetInputData(ii)
        writer.Write()

    print('Done')




                            
if __name__ == '__main__':



    parser = argparse.ArgumentParser(description='Convert BW image to 3D solid (black keep, white remove). ')
    parser.add_argument('-i', '--inputFile', dest='inputFile', help='Input PNG. Required', type=str, required=True)
    parser.add_argument('-o', '--outputFile', dest='outputFile', help='Output STL [default as input, change extn]', type=str, default=None)
    parser.add_argument('-l', '--length', dest='length', help='Output length (int mm). Default, input length', type=int, default=0)
    parser.add_argument('-t', '--thickness', dest='thickness', help='Output thickness (int mm). [default: 3mm]', type=int, default=3)
    parser.add_argument('-I', '--invert', dest='INVERT', help='Invert image', action='store_true')
    parser.add_argument('-IMAGE', '--image', dest='IMAGE', help='Save image', action='store_true')


    #    parser.add_argument('-d',dest='studyNumber',help='Study number of subject. Default=0', type=int, default=0)

    args = parser.parse_args()

    image_to_3D(args.inputFile, args.outputFile, args.length, args.thickness, args.INVERT, IMAGE=args.IMAGE)