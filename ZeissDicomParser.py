#
# Script that parses a dicom file and an IMG file as exported from the
# Zeiss Cirrus OCT machine, and creates a nifti image.
#
# Christos Bergeles
# Robotics and Vision in Medicine Lab
# Wellcome/EPSRC Centre for Interventional and Surgical Sciences
# University College London
#
# 2018.03.28
#

import pydicom
from pydicom import valuerep
import re
import zipfile
from os import walk
import os, sys, getopt
import shutil
import numpy as np
import nibabel


def createNifty(scanType, dataDirectory, properties):
    """
    Parses the dataDirectory to identify the IMGExport folder where the raw data
    are located, and identifies the appropriate file according to scanType. Then,
    using the properties provided, creates a nifty image and saves it.
    :param nifti: the created nifti image.
    :param directoryToRemove: the temporary directory to be removed.
    """
    tmpDir = "/tmp/"  # os.getcwd()

    # Retrieve list of zip files that contain IMG data in root-directory
    zipFilenameList = []
    zipPathList = []
    for (dirpath, dirnames, filenames) in walk(dataDirectory):
        for filename in filenames:
            if "IMGExportFiles.zip" in filename:
                zipFilenameList.append(filename)
                zipPathList.append(dirpath)

    if len(zipFilenameList) > 1:
        print("Error - More than one raw data zipfile detected.")
        exit(1)

    zipFilename = zipFilenameList[0]
    zipPath = zipPathList[0]

    # Unzip the IMG folder
    directoryToCreate = tmpDir + zipFilename[:-4]
    if not os.path.exists(directoryToCreate):
        os.makedirs(directoryToCreate)

    # Grab the entire path of the zip file
    zipFileObject = zipfile.ZipFile(zipPath + zipFilename)

    # Extract it in the newly generated folder
    zipFileObject.extractall(directoryToCreate)

    # Go through all the folders and retrieve all relevant .raw files
    imgFilenameList = []
    for (dirpath, dirnames, filenames) in walk(directoryToCreate):
        for filename in filenames:
            if ( ("cube_raw" in filename) and (scanType in filename) and (scanType in "Macular Cube") ) or \
                ( ("FlowCube_raw" in filename) and (scanType in filename) and ("Angiography 8x8" in scanType) ) or \
                    (("FlowCube_raw" in filename) and (scanType in filename) and ("Angiography 3x3" in scanType)):
                imgFilenameList.append(dirpath + "/" + filename)
    # print(imgFilenameList)

    if len(imgFilenameList) > 1:
        print("Error - More than one raw datafile detected.")
        exit(1)

    imgFilename = imgFilenameList[0]

    # Create fully qualified name to save the image
    if scanType in "Macular Cube":
        outputFileFullyQualifiedName = "macularCube.nii"
    if scanType in "Angiography 3x3":
        outputFileFullyQualifiedName = "angiography3x3.nii"
    if scanType in "Angiography 8x8":
        outputFileFullyQualifiedName = "angiography8x8.nii"

    outputFileFullyQualifiedName  = os.path.join(
        dataDirectory + "/" + outputFileFullyQualifiedName)

    data = np.fromfile(imgFilename, dtype='uint8')

    sliceThicknessInMM = properties[0]
    pixelWidthInMM = properties[1]
    pixelDepthInMM = properties[2]
    imageWidthInPixels = properties[3]
    imageDepthInPixels = properties[4]
    bitDepth = properties[5]

# TODO: Double check that this matches the retrieved number of slices
# TODO: The above was verified manually - CB.
    numSlices = int(len(data) / imageDepthInPixels / imageWidthInPixels)
    data = np.reshape(data, (numSlices, imageDepthInPixels, imageWidthInPixels))
    data = np.moveaxis(data, 0, -1)
    data = np.transpose(data, (1, 0, 2))
    data = np.flip(data, 1)

    # print(np.shape(data))
    niHdr = nibabel.Nifti1Header()
    niHdr.set_data_shape(data.shape)
    niHdr.set_data_dtype(np.uint8)
    niHdr.set_xyzt_units('mm', 'sec')

    sform = np.diag([pixelWidthInMM, pixelDepthInMM, sliceThicknessInMM, 1.0])
    nifti = nibabel.Nifti1Image(data, sform, niHdr)

    nibabel.save(nifti, outputFileFullyQualifiedName)
    print("Nifti image saved at " + outputFileFullyQualifiedName)

    return nifti, directoryToCreate


def retrieveDicomFiles(scanType, dataDirectory):
    """
    Given the scan type (scanType) and the data Directory (dataDirectory), this function finds the zip
    files that correspond to DICOM data, extracts them to a temporary folder, and the identifies
    within them the DICOM files that correspond to DICOM files of the requested scan.
    :param scanType: can be "Macular Cube", "Angiography 3x3", or "Angiography 8x8".
    :param dataDirectory: the root-level directory containing the DICOM data.
    :return: a list of filenames that will then be parsed for relevant volumentric data.
    """

    if "Macular Cube" not in scanType and \
            "Angiography 8x8" not in scanType and \
            "Angiography 3x3" not in scanType:
        print('Error: Only types of ''Macular Cube'', ''Angiography 3x3'', or ''Angiography 8x8'' are expected.')
        exit(1)

    tmpDir = "/tmp/" # os.getcwd()
    cleanUpTempFolders(tmpDir + "IMGExportFiles/")

    # Retrieve list of zip files that contain DICOM data in root-directory
    zipFilenameList = []
    zipPathList = []
    for (dirpath, dirnames, filenames) in walk(dataDirectory):
        for filename in filenames:
            if (".zip" in filename) and ("ExportFiles" not in filename):
                zipFilenameList.append(filename)
                zipPathList.append(dirpath)


    # Unzip the DICOM folders
    directoriesToCreate = []
    for idx in range(0, len(zipFilenameList)):
        zipPath = zipPathList[idx]
        dicomZipFile = zipFilenameList[idx]

        directoryToCreate = tmpDir + dicomZipFile[:-4]

        # Create a directory for the archive
        directoriesToCreate.append(directoryToCreate)
        if not os.path.exists(directoryToCreate):
            os.makedirs(directoryToCreate)

        # Grab the entire path of the zip file
        zipFileObject = zipfile.ZipFile(zipPath + dicomZipFile)

        # Extract it in the newly generated folder
        zipFileObject.extractall(directoryToCreate)

    # Go through all the folders and retrieve all DICOM files
    dcmFilenameList = []
    for dicomDirectory in directoriesToCreate:
        for (dirpath, dirnames, filenames) in walk(dicomDirectory):
            for filename in filenames:
                if ".DCM" in filename:
                    dcmFilenameList.append(dirpath + "/" + filename)

    # Go through all DICOM files and see whether they talk about scanType
    approvedDicomFiles = []
    for dicomFilename in dcmFilenameList:
        dcm = pydicom.dcmread(dicomFilename)
        codeMeaning = dcm[0x40, 0x260][0][0x08, 0x104].value
        if scanType in codeMeaning:
            approvedDicomFiles.append(dicomFilename)

    return directoriesToCreate, approvedDicomFiles


def parseDicom(scanType, dicomFilename):
    """
    Given a DICOM filename, it loads the dicom and returns sliceThicknessMM, imageWidthMM (left-right), imageDepthMM (z),
    imageWidthPix, imageDepthPix, bitDepth.
    :param scanType: can be "Macular Cube", "Angiography 3x3", or "Angiography 8x8".
    :param dicomFilename: the path to the dicom file to be parsed.
    :return: valid, sliceThicknessInMM, pixelWidthInMM, pixelDepthInMM, imageWidthInPixels, imageDepthInPixels, bitDepth
    """
    valid = True

    dcm = pydicom.dcmread(dicomFilename)

    # Get the slice thickness and sanity check it.
    try:
        sliceThicknessInMM = dcm.SpacingBetweenSlices
    except ValueError as e:
        msg = str(e).split(": ")
        sliceThicknessInMM = msg[1]
    except AttributeError as e:
        msg = str(e)
        # print("Error - " + dicomFilename + " - " + msg)
        sliceThicknessInMM = -1.0
        valid = False

    # Remove unicode characters as regular expressions and convert to float
    if type(sliceThicknessInMM) is str:
        sliceThicknessInMM = float(
            re.sub('[^0-9.]', '', sliceThicknessInMM.split('\x00')[0]))

    if type(sliceThicknessInMM) is valuerep.DSfloat:
        sliceThicknessInMM = float(sliceThicknessInMM)

    # Sanity checks
    if sliceThicknessInMM == 0:
        valid = False

    # if "Angiography" in scanType:
        # sliceThicknessInMM = 0

     # Get the number of frames
    try:
        numberOfFrames = dcm.NumberOfFrames
    except AttributeError as e:
        msg = str(e)
        # print("Error - " + dicomFilename + " - " + msg)
        numberOfFrames = -1.0
        valid = False

    # Remove unicode characters as regular expressions and convert to float
    if type(numberOfFrames) is str:
        numberOfFrames = float(
            re.sub('[^0-9.]', '', numberOfFrames.split('\x00')[0]))
    if type(numberOfFrames) is valuerep.DSfloat:
        numberOfFrames = float(numberOfFrames)

    # Sanity check
    if (scanType in "Macular Cube") and (numberOfFrames != 128):
        valid = False

    # Get pixel dimensions
    try:
        pixelSpacing = dcm.PixelSpacing
        pixelSpacing = str(pixelSpacing).split(",")

        pixelWidthInMM = pixelSpacing[0]
        pixelDepthInMM = pixelSpacing[1]
    except ValueError as e:
        msg = str(e).split(": ")
        dims = msg[1].split(",")
        pixelWidthInMM = dims[0]
        pixelDepthInMM = dims[1]
    except AttributeError as e:
        msg = str(e)
        # print("Error - " + dicomFilename + " - " + msg)
        valid = False

    # Remove unicode characters as regular expressions and convert to float
    pixelWidthInMM = float(
        re.sub('[^0-9.]', '', pixelWidthInMM.split('\x00')[0]))
    pixelDepthInMM = float(
        re.sub('[^0-9.]', '', pixelDepthInMM.split('\x00')[0]))

    # Sanity checks
    if pixelWidthInMM == 0 or pixelDepthInMM == 0:
        valid = False

    # Isotropic in pixelWidth and sliceThickness for Angiography
    if "Angiography" in scanType:
        if abs(pixelWidthInMM - sliceThicknessInMM) > 0.0005:
            valid = False

    imageWidthInPixels = dcm.Rows
    imageDepthInPixels = dcm.Columns
    bitDepth = dcm.BitsStored

    if bitDepth != 8:
        print("Error - expecting 8 bit depth - " + bitDepth + " found.")
        valid = False

    # Sanity checks
    if imageWidthInPixels == 0 or imageDepthInPixels == 0 or bitDepth == 0:
        valid = False

    return valid, sliceThicknessInMM, pixelWidthInMM, pixelDepthInMM, imageWidthInPixels, imageDepthInPixels, bitDepth


def aggregateDicomProperties(scanType, dicomFilenames):
    """
    Each DICOM file that is parsed gives a separate set of properties. This function
    aims to find the ones that appear consistently, in order to consider them
    as the final properties for this particular scan.
    :param scanType: can be "Macular Cube", "Angiography 3x3", or "Angiography 8x8".
    :param dicomFilenames: a list of all dicom files to be considered.
    :return: sliceThicknessInMM, pixelWidthInMM, pixelDepthInMM, imageWidthInPixels, imageDepthInPixels, bitDepth
    """
    sliceThicknessInMM = []
    pixelWidthInMM = []
    pixelDepthInMM = []
    imageWidthInPixels = []
    # imageWidthPerPixel = []
    imageDepthInPixels = []
    # imageDepthPerPixel = []
    bitDepth = []

    for dicomFilename in dicomFilenames:
        # print('\nParsing file: ' + dicomFilename)
        properties = parseDicom(scanType, dicomFilename)
        # print("DICOM properties: ")
        # print(properties)
        if properties[0]:
            # sliceThicknessInMM cannot really be more than 1mm
            if (properties[1] > 1.0) or  \
                    properties[4] < 1.0 or \
                    properties[5] < 1.0 or \
                    properties[6] < 4.0:
                # print("Ignoring.")
                break


            sliceThicknessInMM.append(properties[1])
            # imageWidthInMM w.r.t. imageWidthInPixels may be different, so, consider the per pixel value
            pixelWidthInMM.append(properties[2])
            # imageWidthPerPixel.append(properties[2]/properties[4])

            # imageDepthInMM w.r.t. imageDepthInPixels may be different, so, consider the per pixel value
            pixelDepthInMM.append(properties[3])
            # imageDepthPerPixel.append(properties[3]/properties[5])

            imageWidthInPixels.append(properties[4])
            imageDepthInPixels.append(properties[5])
            bitDepth.append(properties[6])


    # Return the average of all values for now. Seems that apart from a size difference,
    # they are all identical.
    sliceThicknessInMM = np.average(np.asarray(sliceThicknessInMM))
    # imageWidthPerPixel = np.average(np.asarray(imageWidthPerPixel))
    # imageDepthPerPixel = np.average(np.asarray(imageDepthPerPixel))
    bitDepth = np.average(np.asarray(bitDepth))

    # imageWidthInMM = imageWidthPerPixel * imageWidthInPixels[0]
    # imageDepthInMM = imageDepthPerPixel * imageDepthInPixels[0]
    pixelWidthInMM = np.average(np.asarray(pixelWidthInMM))
    pixelDepthInMM = np.average(np.asarray(pixelDepthInMM))

    print("\n==" + scanType + "==")
    print("sliceThickness = " + str(1000*sliceThicknessInMM) + " um")
    print("pixelWidth = " + str(1000*pixelWidthInMM) + " um")
    print("pixelDepth = " + str(1000*pixelDepthInMM) + " um")
    print("imageWidthInPixels = " + str(imageWidthInPixels[0]))
    print("imageDepthInPixels = " + str(imageDepthInPixels[0]))
    print("bitDepth = " + str(bitDepth) + "\n")

    return sliceThicknessInMM, pixelWidthInMM, pixelDepthInMM, \
           imageWidthInPixels[0], imageDepthInPixels[0], bitDepth


def cleanUpTempFolders(directoriesToRemove):
    """
    Removes the set of temporary directories that have been created to access
    the DICOM files.
    :param directoriesToRemove: a list of directories to be removed.
    """
    if type(directoriesToRemove) is list or \
            type(directoriesToRemove) is tuple:
        for directoryToRemove in directoriesToRemove:
            # print('Removing temporary directory ' + directoryToRemove)
            shutil.rmtree(directoryToRemove, ignore_errors=True)
    else:
        # print('Removing temporary directory ' + directoriesToRemove)
        shutil.rmtree(directoriesToRemove, ignore_errors=True)


def help():
    print("zeissDICOMParser.py -i <inputdirectory> -t <scantype>")


if __name__ == "__main__":

    # print("Warning - Slice Thickness in Angiography scans is not properly retrieved.")

    recursive = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:t:r", ["inputdirectory=", "scantype=", "recursive="])
    except getopt.GetoptError:
        help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            help()
            sys.exit()
        elif opt in ("-i", "--inputdirectory"):
            dataDirectory = arg + "/"
        elif opt in ("-t", "--scantype"):
            scanType = arg
        elif opt in ("-r", "--recursive"):
            recursive = True
            print("Parsing recursively.")

    if scanType == "All" or scanType == "all":
        scanTypes = ["Macular Cube", "Angiography 8x8", "Angiography 3x3"]
        print("Parsing all scans.")
    else:
        scanTypes = []
        scanTypes.append(scanType)

    dataDirectories = []
    if not recursive:
        dataDirectories.append(dataDirectory)
    else:
        for (root, subdirs, files) in os.walk(dataDirectory):
            for subdir in subdirs:
                if "RIDE_" in subdir:
                    dataDirectories.append(root + subdir + "/")

    for dataDirectory in dataDirectories:
        try:
            for scanType in scanTypes:
                print("Parsing " + dataDirectory + ".")
                tmpDirectoriesCreated, dicomFilenames = retrieveDicomFiles(scanType, dataDirectory)
                properties = aggregateDicomProperties(scanType, dicomFilenames)
                cleanUpTempFolders(tmpDirectoriesCreated)

                nifti, tmpDirectoriesCreated = createNifty(scanType, dataDirectory, properties)
                cleanUpTempFolders(tmpDirectoriesCreated)
        except:
            print("Omit this directory.")



#  according to scantype find file in imgexports.zip
# for oct find dcm files that correspond to scantype angiography.

