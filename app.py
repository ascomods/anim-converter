import fbx
import fbxsip
from core.SPA import SPA
import os, sys, glob

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

def spaExportToFbx(path, fbxScene):
    spaName = os.path.basename(path)
    spaObject = SPA(spaName)
    stream = open(path, "rb")
    spaObject.read(stream)

    rootNode = fbxScene.GetRootNode()
    time = fbx.FbxTime()
    time.SetFrame(0)

    # Retrieving wanted animation
    animStack = fbx.FbxAnimStack.Create(fbxScene, spaName)
    animLayer = fbx.FbxAnimLayer.Create(fbxScene, "")
    animStack.AddMember(animLayer)
    
    for boneName in spaObject.data:
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

        i = 0
        for frameNum in spaObject.data[boneName]:
            time.SetFrame(frameNum)

            if 'translation' in spaObject.data[boneName][frameNum]:
                transX = node.LclTranslation.Get()[0]
                transY = node.LclTranslation.Get()[1]
                transZ = node.LclTranslation.Get()[2]

                transX += spaObject.data[boneName][frameNum]['translation'][2]
                transY += spaObject.data[boneName][frameNum]['translation'][1]
                transZ += spaObject.data[boneName][frameNum]['translation'][0]

                keyIndex = transXCurve.KeyAdd(time)[0]
                transXCurve.KeySet(keyIndex, time, transX, fbx.FbxAnimCurveDef.eInterpolationConstant)
                keyIndex = transYCurve.KeyAdd(time)[0]
                transYCurve.KeySet(keyIndex, time, transY, fbx.FbxAnimCurveDef.eInterpolationConstant)
                keyIndex = transZCurve.KeyAdd(time)[0]
                transZCurve.KeySet(keyIndex, time, transZ, fbx.FbxAnimCurveDef.eInterpolationConstant)
            
            if 'rotation' in spaObject.data[boneName][frameNum]:
                rotX = node.LclRotation.Get()[0]
                rotY = node.LclRotation.Get()[1]
                rotZ = node.LclRotation.Get()[2]
                
                rotX += spaObject.data[boneName][frameNum]['rotation'][2]
                rotY += spaObject.data[boneName][frameNum]['rotation'][1]
                rotZ += spaObject.data[boneName][frameNum]['rotation'][0]

                keyIndex = rotXCurve.KeyAdd(time)[0]
                rotXCurve.KeySet(keyIndex, time, rotX, fbx.FbxAnimCurveDef.eInterpolationConstant)
                keyIndex = rotYCurve.KeyAdd(time)[0]
                rotYCurve.KeySet(keyIndex, time, rotY, fbx.FbxAnimCurveDef.eInterpolationConstant)
                keyIndex = rotZCurve.KeyAdd(time)[0]
                rotZCurve.KeySet(keyIndex, time, rotZ, fbx.FbxAnimCurveDef.eInterpolationConstant)
            i += 1

        rotXCurve.KeyModifyEnd()
        rotYCurve.KeyModifyEnd()
        rotZCurve.KeyModifyEnd()

        transXCurve.KeyModifyEnd()
        transYCurve.KeyModifyEnd()
        transZCurve.KeyModifyEnd()

def fbxExportToSpa(path, fbxScene, importer):
    # Init selection criteria
    animStackClassIdCriteria = fbx.FbxCriteria.ObjectType(fbx.FbxAnimStack.ClassId)
    animLayerClassIdCriteria = fbx.FbxCriteria.ObjectType(fbx.FbxAnimLayer.ClassId)
    skeletonCriteria = fbx.FbxCriteria.ObjectType(fbx.FbxSkeleton.ClassId)

    animStackCount = fbxScene.GetSrcObjectCount(animStackClassIdCriteria)
    boneCount = fbxScene.GetSrcObjectCount(skeletonCriteria)
    rootNode = fbxScene.GetRootNode()

    animData = {}
    frameCounts = {}
    
    for i in range(animStackCount):
        animStack = fbxScene.GetSrcObject(animStackClassIdCriteria, i)
        animLayerCount = animStack.GetSrcObjectCount(animLayerClassIdCriteria)

        spaName = os.path.splitext(os.path.basename(animStack.GetName()))[0]
        if "|" in spaName:
            spaName = spaName.split("|")[-1]
        spaName += ".spa"
        animData[spaName] = {'NULL': {0: {'translation': (0,0,0,1), 'rotation': (0,0,0)}}}

        lFilter = fbx.FbxAnimCurveFilterUnroll()
        lFilter.Reset()
        lFilter.SetTestForPath(True)
        lFilter.SetForceAutoTangents(True)
        lFilter.SetQualityTolerance(0.25)
        lFilter.Apply(animStack)

        if spaName != 'Default.spa':
            takeInfo = importer.GetTakeInfo(i - 1)
            timeMode = fbx.FbxTime.GetGlobalTimeMode()
            start = takeInfo.mLocalTimeSpan.GetStart()
            startFrame = start.GetFrameCount(timeMode)
            stop = takeInfo.mLocalTimeSpan.GetStop()
            stopFrame = stop.GetFrameCount(timeMode)

            frameCount = int(stopFrame - startFrame)
            frameCounts[spaName] = frameCount

        for j in range(animLayerCount):
            animLayer = animStack.GetSrcObject(animLayerClassIdCriteria, j)
            node = rootNode.FindChild("NULL")
            animData[spaName] = \
                getNodeAnimationData(animData[spaName], node, animLayer)
            
            for k in range(boneCount):
                node = fbxScene.GetSrcObject(skeletonCriteria, k).GetNode()
                animData[spaName] = \
                    getNodeAnimationData(animData[spaName], node, animLayer)

    for spaName in animData:
        if spaName != 'Default.spa':
            animData[spaName] = cleanData(animData['Default.spa'], animData[spaName], spaName)
            spaObject = SPA(spaName)
            stream = open(f'{path}/{spaName}', "wb")
            spaObject.load(animData[spaName], frameCounts[spaName])
            spaObject.write(stream)

# Remove position and rotation offsets from the default pose + cleaning redundant frames
def cleanData(offsetData, data, animName):
    for boneName in data:
        for frame in list(data[boneName].keys()):
            if 'translation' in data[boneName][frame]:
                data[boneName][frame]['translation'] = tuple(map(lambda i, j: i - j, \
                    data[boneName][frame]['translation'], offsetData[boneName][0]['translation']))
                if data[boneName][frame]['translation'] != (0,0,0,1):
                        data[boneName][frame]['translation'] = (*data[boneName][frame]['translation'][:3],1)
                else:
                    del data[boneName][frame]['translation']
            if 'rotation' in data[boneName][frame]:
                data[boneName][frame]['rotation'] = tuple(map(lambda i, j: i - j, \
                    data[boneName][frame]['rotation'], offsetData[boneName][0]['rotation']))
                if data[boneName][frame]['rotation'] == (0,0,0):
                    del data[boneName][frame]['rotation']
            if data[boneName][frame] == {}:
                del data[boneName][frame]
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
        frame = transXCurve.KeyGetTime(i).GetFrameCount()
        translation = (transZCurve.KeyGetValue(i), transYCurve.KeyGetValue(i), transXCurve.KeyGetValue(i), 1)
        if translation != (0,0,0,1):
            if frame not in animData[node.GetName()]:
                animData[node.GetName()][frame] = {}
            animData[node.GetName()][frame]['translation'] = translation

    for i in range(rotXCurve.KeyGetCount()):
        frame = rotXCurve.KeyGetTime(i).GetFrameCount()
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
        if ext.lower() == '.spa' and os.path.isfile(args[3]):
            loadInitialFbx(fbxScene)
            spaExportToFbx(args[3], fbxScene)
        elif os.path.isdir(args[3]):
            outputFormat = args[1].split('=')[1]
            if outputFormat.lower() == 'fbx':
                loadInitialFbx(fbxScene)
                for path in glob.glob(f'{args[3]}/**'):
                    spaExportToFbx(path, fbxScene)
            elif outputFormat.lower() == 'spa':
                fbxExportToSpa(args[3], fbxScene, importer)
                print('FBX --> SPA Export done !')
            else:
                raise Exception("invalid output path")
        else:
            raise Exception("invalid SPA input/output folder")

        # Saving fbx output
        if len(args) == 5:
            name, ext = os.path.splitext(os.path.basename(args[4]))
            if ext.lower() == '.fbx':
                saveScene(args[4], fbxManager, fbxScene)
                print('SPA --> FBX Export done !')
        
        importer.Destroy()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f'USAGE:\n'
              f'SPA TO FBX: anim_converter.exe --to=fbx noesis.fbx (spa_folder|input.spa) output.fbx\n'
              f'FBX TO SPA: anim_converter.exe --to=spa input.fbx spa_folder'
        )
    elif len(sys.argv) >= 4:
        handleInput(sys.argv)