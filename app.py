import fbx
import fbxsip
from core.SPA import SPA
from core.ANM import ANM
import os, sys, glob
import math

def getASCIIFormatIndex( pManager ):
    ''' Obtain the index of the ASCII export format. '''
    # Count the number of formats we can write to.
    numFormats = pManager.GetIOPluginRegistry().GetWriterFormatCount()

    # Set the default format to the native binary format.
    formatIndex = pManager.GetIOPluginRegistry().GetNativeWriterFormat()

    # Get the FBX format index whose corresponding description contains "ascii".
    for i in range( 0, numFormats ):

        # First check if the writer is an FBX writer.
        if pManager.GetIOPluginRegistry().WriterIsFBX( i ):

            # Obtain the description of the FBX writer.
            description = pManager.GetIOPluginRegistry().GetWriterFormatDescription( i )

            # Check if the description contains 'ascii'.
            if 'ascii' in description:
                formatIndex = i
                break

    # Return the file format.
    return formatIndex

def saveScene( pFilename, pFbxManager, pFbxScene, pAsASCII=False ):
    ''' Save the scene using the Python FBX API '''
    exporter = fbx.FbxExporter.Create( pFbxManager, '' )

    if pAsASCII:
        #DEBUG: Initialize the FbxExporter object to export in ASCII.
        asciiFormatIndex = getASCIIFormatIndex( pFbxManager )
        isInitialized = exporter.Initialize( pFilename, asciiFormatIndex )
    else:
        isInitialized = exporter.Initialize( pFilename )

    if( isInitialized == False ):
        raise Exception( 'Exporter failed to initialize. Error returned: ' + str( exporter.GetLastErrorString() ) )

    exporter.Export( pFbxScene )

    exporter.Destroy()

# Retrieve fbx file and add default pose to animation layers
def loadInitialFbx(fbxScene):
    skeletonCriteria = fbx.FbxCriteria.ObjectType(fbx.FbxSkeleton.ClassId)
    boneCount = fbxScene.GetSrcObjectCount(skeletonCriteria)
    time = fbx.FbxTime()
    time.SetFrame(0)

    # Setting up animation stack
    animStack = fbx.FbxAnimStack.Create(fbxScene, "Default")
    animLayer = fbx.FbxAnimLayer.Create(fbxScene, "")
    animStack.AddMember(animLayer)
    
    # Retrieving default pose
    for i in range(boneCount):
        node = fbxScene.GetSrcObject(skeletonCriteria, i).GetNode()
        transX = node.LclTranslation.Get()[0]
        transY = node.LclTranslation.Get()[1]
        transZ = node.LclTranslation.Get()[2]

        transXCurve = node.LclTranslation.GetCurve(animLayer, 'X', True)
        transYCurve = node.LclTranslation.GetCurve(animLayer, 'Y', True)
        transZCurve = node.LclTranslation.GetCurve(animLayer, 'Z', True)

        keyIndex = transXCurve.KeyAdd(time)[0]
        transXCurve.KeySet(keyIndex, time, transX, fbx.FbxAnimCurveDef.eInterpolationConstant)
        keyIndex = transYCurve.KeyAdd(time)[0]
        transYCurve.KeySet(keyIndex, time, transY, fbx.FbxAnimCurveDef.eInterpolationConstant)
        keyIndex = transZCurve.KeyAdd(time)[0]
        transZCurve.KeySet(keyIndex, time, transZ, fbx.FbxAnimCurveDef.eInterpolationConstant)
        
        rotX = node.LclRotation.Get()[0]
        rotY = node.LclRotation.Get()[1]
        rotZ = node.LclRotation.Get()[2]

        rotXCurve = node.LclRotation.GetCurve(animLayer, 'X', True)
        rotYCurve = node.LclRotation.GetCurve(animLayer, 'Y', True)
        rotZCurve = node.LclRotation.GetCurve(animLayer, 'Z', True) 

        keyIndex = rotXCurve.KeyAdd(time)[0]
        rotXCurve.KeySet(0, time, rotX, fbx.FbxAnimCurveDef.eInterpolationConstant)
        keyIndex = rotYCurve.KeyAdd(time)[0]
        rotYCurve.KeySet(0, time, rotY, fbx.FbxAnimCurveDef.eInterpolationConstant)
        keyIndex = rotZCurve.KeyAdd(time)[0]
        rotZCurve.KeySet(0, time, rotZ, fbx.FbxAnimCurveDef.eInterpolationConstant)

def exportToFbx(path, fbxScene, inputClass):
    inputName = os.path.basename(path)
    inputObject = eval(inputClass.upper())(inputName)
    stream = open(path, "rb")
    inputObject.read(stream)

    rootNode = fbxScene.GetRootNode()
    time = fbx.FbxTime()
    time.SetGlobalTimeMode(fbx.FbxTime.ePAL)
    time.SetFrame(0)

    # Retrieving wanted animation
    animStack = fbx.FbxAnimStack.Create(fbxScene, inputName)
    animLayer = fbx.FbxAnimLayer.Create(fbxScene, "")
    animStack.AddMember(animLayer)
    
    for boneName in inputObject.data:
        node = rootNode.FindChild(boneName)

        # Getting TR curves
        transXCurve = node.LclTranslation.GetCurve(animLayer, 'X', True)
        transYCurve = node.LclTranslation.GetCurve(animLayer, 'Y', True)
        transZCurve = node.LclTranslation.GetCurve(animLayer, 'Z', True)

        rotXCurve = node.LclRotation.GetCurve(animLayer, 'X', True)
        rotYCurve = node.LclRotation.GetCurve(animLayer, 'Y', True)
        rotZCurve = node.LclRotation.GetCurve(animLayer, 'Z', True)

        transXCurve.KeyModifyBegin()
        transYCurve.KeyModifyBegin()
        transZCurve.KeyModifyBegin()

        rotXCurve.KeyModifyBegin()
        rotYCurve.KeyModifyBegin()
        rotZCurve.KeyModifyBegin()

        for frameNum in inputObject.data[boneName]:
            time.SetFrame(frameNum)

            if 'translation' in inputObject.data[boneName][frameNum]:
                transX = node.LclTranslation.Get()[0]
                transY = node.LclTranslation.Get()[1]
                transZ = node.LclTranslation.Get()[2]

                transX += inputObject.data[boneName][frameNum]['translation'][0]
                transY += inputObject.data[boneName][frameNum]['translation'][1]
                transZ += inputObject.data[boneName][frameNum]['translation'][2]

                keyIndex = transXCurve.KeyAdd(time)[0]
                transXCurve.KeySet(keyIndex, time, transX, fbx.FbxAnimCurveDef.eInterpolationConstant)
                keyIndex = transYCurve.KeyAdd(time)[0]
                transYCurve.KeySet(keyIndex, time, transY, fbx.FbxAnimCurveDef.eInterpolationConstant)
                keyIndex = transZCurve.KeyAdd(time)[0]
                transZCurve.KeySet(keyIndex, time, transZ, fbx.FbxAnimCurveDef.eInterpolationConstant)
            
            if 'rotation' in inputObject.data[boneName][frameNum]:
                rotX = node.LclRotation.Get()[0]
                rotY = node.LclRotation.Get()[1]
                rotZ = node.LclRotation.Get()[2]
            
                rotX += inputObject.data[boneName][frameNum]['rotation'][0]
                rotY += inputObject.data[boneName][frameNum]['rotation'][1]
                rotZ += inputObject.data[boneName][frameNum]['rotation'][2]

                keyIndex = rotXCurve.KeyAdd(time)[0]
                rotXCurve.KeySet(keyIndex, time, rotX, fbx.FbxAnimCurveDef.eInterpolationConstant)
                keyIndex = rotYCurve.KeyAdd(time)[0]
                rotYCurve.KeySet(keyIndex, time, rotY, fbx.FbxAnimCurveDef.eInterpolationConstant)
                keyIndex = rotZCurve.KeyAdd(time)[0]
                rotZCurve.KeySet(keyIndex, time, rotZ, fbx.FbxAnimCurveDef.eInterpolationConstant)
    
        rotXCurve.KeyModifyEnd()
        rotYCurve.KeyModifyEnd()
        rotZCurve.KeyModifyEnd()

        transXCurve.KeyModifyEnd()
        transYCurve.KeyModifyEnd()
        transZCurve.KeyModifyEnd()

def fbxExport(fbxInput, path, outputClass):
    defaultAnimData = None
    defaultName = ""
    try:
        defaultAnimData = getAnimationData(f"resources/fbx/{outputClass.lower()}_t_pose.fbx", outputClass, False)
        defaultName = list(defaultAnimData.keys())[0]
    except:
        pass
    animData, frameCounts = getAnimationData(fbxInput, outputClass)

    animData = roundData(animData)
    for outputName in animData:
        if defaultAnimData != None and defaultName != "":
            animData[outputName] = cleanData(animData[outputName], defaultAnimData[defaultName])
        outputObject = eval(outputClass.upper())(outputName)
        stream = open(f'{path}/{outputName}', "wb")
        outputObject.load(animData[outputName], frameCounts[outputName])
        outputObject.write(stream)

def getAnimationData(path, outputClass, withFrameCount = True):
    fbxManager = fbx.FbxManager.Create()
    fbxScene = fbx.FbxScene.Create(fbxManager, '')
    importer = fbx.FbxImporter.Create(fbxManager, '')
    
    ios = fbx.FbxIOSettings.Create(fbxManager, fbx.IOSROOT)
    importer.Initialize(path, -1, ios)
    importer.Import(fbxScene)

    # Init selection criteria
    animStackClassIdCriteria = fbx.FbxCriteria.ObjectType(fbx.FbxAnimStack.ClassId)
    animLayerClassIdCriteria = fbx.FbxCriteria.ObjectType(fbx.FbxAnimLayer.ClassId)
    skeletonCriteria = fbx.FbxCriteria.ObjectType(fbx.FbxSkeleton.ClassId)

    animStackCount = fbxScene.GetSrcObjectCount(animStackClassIdCriteria)
    boneCount = fbxScene.GetSrcObjectCount(skeletonCriteria)
    rootNode = fbxScene.GetRootNode()

    animData = {}
    frameCounts = {}

    rootBoneName = eval(outputClass.upper()).boneList[0]
    for i in range(animStackCount):
        animStack = fbxScene.GetSrcObject(animStackClassIdCriteria, i)
        animLayerCount = animStack.GetSrcObjectCount(animLayerClassIdCriteria)

        outputName = os.path.splitext(os.path.basename(animStack.GetName()))[0]
        if "|" in outputName:
            outputName = outputName.split("|")[-1]
        outputName += f".{outputClass.lower()}"
        animData[outputName] = {rootBoneName: {0: {'translation': (0,0,0,1), 'rotation': (0,0,0)}}}

        lFilter = fbx.FbxAnimCurveFilterUnroll()
        lFilter.Reset()
        lFilter.SetTestForPath(True)
        lFilter.SetForceAutoTangents(True)
        lFilter.SetQualityTolerance(0.25)
        lFilter.Apply(animStack)

        if withFrameCount:
            takeInfo = importer.GetTakeInfo(i)
            timeMode = fbx.FbxTime.ePAL # GetGlobalTimeMode
            start = takeInfo.mLocalTimeSpan.GetStart()
            startFrame = start.GetFrameCount(timeMode)
            stop = takeInfo.mLocalTimeSpan.GetStop()
            stopFrame = stop.GetFrameCount(timeMode)
            frameCounts[outputName] = int(stopFrame - startFrame)

        for j in range(animLayerCount):
            animLayer = animStack.GetSrcObject(animLayerClassIdCriteria, j)
            node = rootNode.FindChild(rootBoneName)
            animData[outputName] = \
                getNodeAnimationData(animData[outputName], node, animLayer)
            
            for k in range(boneCount):
                node = fbxScene.GetSrcObject(skeletonCriteria, k).GetNode()
                animData[outputName] = \
                    getNodeAnimationData(animData[outputName], node, animLayer)
    
    importer.Destroy()
    fbxScene.Destroy()
    fbxManager.Destroy()

    if withFrameCount:
        return animData, frameCounts
    else:
        return animData

# Remove position and rotation offsets from the default pose + cleaning redundant frames
def cleanData(data, offsetData = None):
    for boneName in data:
        lastTransFrame = 0
        lastRotFrame = 0

        for frame in list(data[boneName].keys()):
            if 'translation' in data[boneName][frame]:
                if (frame > 0) and ('translation' in data[boneName][lastTransFrame]) and \
                    math.isclose(data[boneName][frame]['translation'][0], data[boneName][lastTransFrame]['translation'][0], rel_tol=0.001) and \
                    math.isclose(data[boneName][frame]['translation'][1], data[boneName][lastTransFrame]['translation'][1], rel_tol=0.001) and \
                    math.isclose(data[boneName][frame]['translation'][2], data[boneName][lastTransFrame]['translation'][2], rel_tol=0.001):
                    del data[boneName][frame]['translation']
                else:
                    lastTransFrame = frame
            if 'rotation' in data[boneName][frame]:
                if (frame > 0) and ('rotation' in data[boneName][lastRotFrame]) and \
                    math.isclose(data[boneName][frame]['rotation'][0], data[boneName][lastRotFrame]['rotation'][0], rel_tol=0.001) and \
                    math.isclose(data[boneName][frame]['rotation'][1], data[boneName][lastRotFrame]['rotation'][1], rel_tol=0.001) and \
                    math.isclose(data[boneName][frame]['rotation'][2], data[boneName][lastRotFrame]['rotation'][2], rel_tol=0.001):
                    del data[boneName][frame]['rotation']
                else:
                    lastRotFrame = frame
            if data[boneName][frame] == {}:
                del data[boneName][frame]
        
        if offsetData != None:
            for frame in list(data[boneName].keys()):
                if 'translation' in data[boneName][frame]:
                    if 0 in offsetData[boneName] and 'translation' in offsetData[boneName][0]:
                        data[boneName][frame]['translation'] = tuple(map(lambda i, j: i - j, \
                            data[boneName][frame]['translation'], offsetData[boneName][0]['translation']))
                    if data[boneName][frame]['translation'] != (0,0,0,1):
                            data[boneName][frame]['translation'] = (*data[boneName][frame]['translation'][:3],1)
                    else:
                        del data[boneName][frame]['translation']
                if 'rotation' in data[boneName][frame]:
                    if 0 in offsetData[boneName] and 'rotation' in offsetData[boneName][0]:
                        data[boneName][frame]['rotation'] = tuple(map(lambda i, j: i - j, \
                            data[boneName][frame]['rotation'], offsetData[boneName][0]['rotation']))
                    if data[boneName][frame]['rotation'] == (0,0,0):
                        del data[boneName][frame]['rotation']
                if data[boneName][frame] == {}:
                    del data[boneName][frame]
    return data

def roundData(data):
    for animName in data:
        for boneName in data[animName]:
            for frame in data[animName][boneName]:
                if 'translation' in data[animName][boneName][frame]:
                    data[animName][boneName][frame]['translation'] = \
                        tuple(map(lambda x: isinstance(x, float) and round(x, 4) or x, \
                            data[animName][boneName][frame]['translation']))
                if 'rotation' in data[animName][boneName][frame]:
                    data[animName][boneName][frame]['rotation'] = \
                        tuple(map(lambda x: isinstance(x, float) and round(x, 4) or x, \
                            data[animName][boneName][frame]['rotation']))
    return data

def getNodeAnimationData(animData, node, animLayer):
    if node.GetName() not in animData:
        animData[node.GetName()] = {}
    
    # Getting TR curves
    transXCurve = node.LclTranslation.GetCurve(animLayer, 'X', True)
    transYCurve = node.LclTranslation.GetCurve(animLayer, 'Y', True)
    transZCurve = node.LclTranslation.GetCurve(animLayer, 'Z', True)

    rotXCurve = node.LclRotation.GetCurve(animLayer, 'X', True)
    rotYCurve = node.LclRotation.GetCurve(animLayer, 'Y', True)
    rotZCurve = node.LclRotation.GetCurve(animLayer, 'Z', True)

    for i in range(transXCurve.KeyGetCount()):
        time = transXCurve.KeyGetTime(i)
        time.SetGlobalTimeMode(fbx.FbxTime.ePAL)
        frame = time.GetFrameCount()
        translation = (transZCurve.KeyGetValue(i), transYCurve.KeyGetValue(i), transXCurve.KeyGetValue(i), 1)
        if translation != (0,0,0,1):
            if frame not in animData[node.GetName()]:
                animData[node.GetName()][frame] = {}
            animData[node.GetName()][frame]['translation'] = translation

    for i in range(rotXCurve.KeyGetCount()):
        time = rotXCurve.KeyGetTime(i)
        time.SetGlobalTimeMode(fbx.FbxTime.ePAL)
        frame = time.GetFrameCount()
        rotation = (rotXCurve.KeyGetValue(i), rotYCurve.KeyGetValue(i), rotZCurve.KeyGetValue(i))
        if rotation != (0,0,0):
            if frame not in animData[node.GetName()]:
                animData[node.GetName()][frame] = {}
            animData[node.GetName()][frame]['rotation'] = rotation

    return animData

def handleInput(args):    
    name, ext = os.path.splitext(os.path.basename(args[2]))

    if ext.lower() == '.fbx':
        global fbxManager
        fbxManager = fbx.FbxManager.Create()
        fbxScene = fbx.FbxScene.Create(fbxManager, '')
        importer = fbx.FbxImporter.Create(fbxManager, '')
        
        ios = fbx.FbxIOSettings.Create(fbxManager, fbx.IOSROOT)
        importer.Initialize(args[2], -1, ios)
        importer.Import(fbxScene)

        if not os.path.exists(args[3]):
            os.mkdir(args[3])

        name, ext = os.path.splitext(os.path.basename(args[3]))
        outputFormat = args[1].split('=')[1]
        if os.path.isfile(args[3]):
            exportToFbx(args[3], fbxScene, ext[1:])
        elif os.path.isdir(args[3]):
            if outputFormat.lower() == 'fbx':
                for path in glob.glob(f'{args[3]}/**'):
                    name, ext = os.path.splitext(os.path.basename(path))
                    exportToFbx(path, fbxScene, ext[1:])
            else:
                fbxExport(args[2], args[3], outputFormat)
                print(f'FBX --> {outputFormat.upper()} Export done !')
        else:
            raise Exception("invalid input/output folder")

        # Saving fbx output
        if len(args) == 5:
            name, ext = os.path.splitext(os.path.basename(args[4]))
            if ext.lower() == '.fbx':
                saveScene(args[4], fbxManager, fbxScene)
                print('FBX Export done !')
        
        importer.Destroy()

if __name__ == "__main__":
   if len(sys.argv) < 4:
       print(f'USAGE:\n'
             f'ANM TO FBX: anim_converter.exe --to=fbx input.fbx (anm_folder|input.anm) output.fbx\n'
             f'FBX TO ANM: anim_converter.exe --to=anm input.fbx output_folder\n'
             f'-----------------------------------------------------------------------------------\n'
             f'SPA TO FBX: anim_converter.exe --to=fbx input.fbx (spa_folder|input.spa) output.fbx\n'
             f'FBX TO SPA: anim_converter.exe --to=spa input.fbx output_folder'
       )
   elif len(sys.argv) >= 4:
       handleInput(sys.argv)