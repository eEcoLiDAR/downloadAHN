#!/usr/bin/env python3


"""
Downloader for (AHN) datasets. Used with eEcoLiDAR project


"""



import argparse, time, traceback, sys, os, shutil, multiprocessing, json
import urllib.request
import datetime
import email.utils as eut
import numpy as np


def argument_parser():
    parser = argparse.ArgumentParser(description="""This script checks compares a local repository of (AHN .LAZ) point cloud data fileas against
    the online AHN repository and downloads any new or updated files. Can be run on a single machine or in distributrd fashion across multiple VMs.
    Division of labour is handeled internally and reproducibly.""")

    parser.add_argument('-l','--localrepository',default='', help='path to local repository', type=str, required=True)
    parser.add_argument('-o','--outputdirectory',default='.',help='full path of desired output directory; download destination',type=str, required=True)
    parser.add_argument('-u','--baseurl',default='',help='common base url of files to be downloaded',type=str, required=True)
    parser.add_argument('-s','--suffix',default=None,help='common suffix of files to be downloaded. Optional if included in other fashion, e.g. in filename',type=str)
    parser.add_argument('-p','--proc',default=1,help='number of processes; default is 1',type=int)
    parser.add_argument('-i','--inputlist',default=None,help='optional input list')
    parser.add_argument('-c','--copylocal',default='False',help='Flag [True,False]. if true up-to-date files from local repository will be copied to output directory')
    parser.add_argument('-t','--tag',default=str(np.random.randint(200000)),help='unique run identifier. If not set a string representation of a random integer in [0,199999) is used.')
    return parser



def build_file_identifiers(inputItem,baseurl,suffix)
    filename = build_filename(inputItem,suffix)
    url = build_url(baseurl,filename)
    return filename, url

def build_filename(top10nlMapTile, suffix):
    if suffix != None:
        filename=top10nlMapTile.lower()+suffix
    else:
        top10nlMapTile.lower()
    return filename


def build_url(baseurl,top10nlMapTileFileName):
    url = baseurl+top10nlMapTileFileName
    return url


def check_local(top10nlMapTile,localFilesPath, suffix):


    mapTileFileName = build_filename(top10nlMapTile,suffix)
    mapTileFileExistsLocal=False

    localMapTileFilePath = os.path.join(localFilesPath,mapTileFileName)

    localSize=[]
    localDate=[]

    if os.path.isfile(localMapTileFilePath):
        mapTileFileExistsLocal=True
        localDate = datetime.datetime.fromtimestamp(os.stat(localMapTileFilePath).st_mtime)
        localSize = os.stat(localMapTileFilePath).st_size

    else:
        pass

    return mapTileFileExistsLocal, localSize, localDate


def check_remote(top10nlMapTile, baseurl, suffix):

    mapTileFileName = build_filename(top10nlMapTile, suffix)
    mapTileFileUrl = build_url(baseurl, mapTileFileName)

    mapTileFileExistsRemote=False
    remoteSize=[]
    remoteDate=[]

    try:
        req = urllib.request.urlopen(mapTileFileUrl)
        mapTileFileExistsRemote=True
        remoteDate = datetime.datetime(*eut.parsedate(req.headers['Last-Modified'])[:6])


    except urllib.error.URLError as e:
        print(e)

    return mapTileFileExistsRemote, remoteSize, remoteDate




def copy_execute(top10nlMapTile, suffix,localFilesPath,outputDirectory):

    mapTileFileName = build_filename(top10nlMapTile, suffix)
    localSrcPath = os.path.join(localFilesPath,mapTileFileName)
    #localDestPath = ps.path.join(outputDirectory,mapTileFileName)
    copySuccess = False


    try:
        shutil.copy2(localSrcPath,outputDirectory)
        copySuccess = True
    except:
        print('failed to copy file {} to {}'.format(localSrcPath,outputDirectory))

    return copySuccess




def download_decider(top10nlMapTile, localFilesPath, baseurl, suffix):

    mapTileFileExistsLocal, localSize, localDate = check_local(top10nlMapTile,localFilesPath, suffix)

    mapTileFileExistsRemote, remoteSize, remoteDate = check_remote(top10nlMapTile, baseurl, suffix)

    download=False

    if mapTileFileExistsRemote == True:
        if mapTileFileExistsLocal == False:
            download = True
        else:
            if ((remoteDate > localDate) or (remoteSize != localSize)):
                download = True
    else:
        if mapTileFileExistsLocal == True:
            print('Unclear origin of data for {}'.format(top10nlMapTile))


    return download, mapTileFileExistsLocal



def download_execute(top10nlMapTile, baseurrl, suffix, outputDir):

    mapTileFileName = build_filename(top10nlMapTile,suffix)
    mapTileFileUrl = build_url(baseurl, mapTileFileName)

    outputFilePath = os.path.join(outputDir,mapTileFileName)
    downloadSuccess = False

    try:
        urllib.request.urlretrieve(mapTileFileUrl,outputFilePath)
        downloadSuccess = True
    except urllib.error.URLError:
        print('failure while downloading')

    return downloadSuccess



def maptile_downloader(top10nlMapTile,localFilesPath,outputDir,baseurl, suffix, copylocal):

    executeDownload, localExists = download_decider(top10nlMapTile,localFilesPath, baseurl, suffix)

    downloadSuccess = False
    executeCopy = False
    copySuccess = False

    if executeDownload == True:

        downloadSuccess = download_execute(top10nlMapTile,baseurl, suffix, outputDir)

    else:
        if localExists == True:
            print('mapTile {} exists and is up-to-date'.format(top10nlMapTile))
            if copylocal == False:
                print('skipping download')
            else:
                print('skipping download. copying from local repository to output directory')
                executeCopy=True
                if localFilesPath == outputDir:
                    print('in place no copy necessary')
                    copySuccess = True
                else:
                    copySuccess = copy_execute(top10nlMapTile,suffix, localFilesPath,outputDir)
        else:
            print('neither local nor remote tile {} found'.format(top10nlMapTile))


    time.sleep(1)
    return executeDownload, downloadSuccess, executeCopy, copySuccess


def read_input(infile):

    tileList=[]
    try:
        with open(infile,'r') as inf:
            lines = inf.readlines()
            tileList = [line.rstrip() for line in lines]

    except IOerror:
        print('input file {} could not be opened.'.format(infile))

    return tileList


def run(localFilesPath,outputDir, baseurl, suffix, numberProcs tag, inputList=[],copylocal=False):
    #check input
    if not os.path.isdir(localFilesPath):
        raise Exception('Error: local file path is not a valid directory!')
    elif os.path.isfile(outputDir):
        raise Exception('Error: file with same name as output directory exists! Please delete it.')

    #Create queues for distributed multiprocessing
    tasksQueue = multiprocessing.Queue()
    resultsQueue = multiprocessing.Queue()

    #add tiles to task queues
    lengthInputList=len(inputList)
    for i in range(lengthInputList):
        tasksQueue.put(inputList[i])
    for i in range(numberProcs): #add as many None jobs as processes toensure terminantion (queue id FIFO)
        tasksQueue.put(None)

    processes = []
    #start number of user processes corresponding to declared numberProcs
    for i in range(numberProcs):
        processes.append(multiprocessing.Process(target=runTileDownloadProc,args=(i,tasksQueue,resultsQueue,localFilesPath,outputDir, baseurl, suffix,copylocal)))
        processes[-1].start()

    downloadList =[]
    for i in range(lengthInputList):
        results = resultsQueue.get()
        downloadList.append(results)
        print('Completed {0} of {1} {2} %'.format(i+1, lengthInputList,100.*(float(i+1)/lengthInputList)))

    for i in range(numberProcs):
        processes[i].join()

    downloadDict = {downloadListElement[0]:downloadListElement[1:] for downloadListElement in downloadList}

    now = datetime.datetime.now()
    legacyjs = '/downloadList'+'-'+str(tag)+'-'+str(now.timestamp())+'.js'
    currentjs = '/downloadList'+'-'+str(tag)+'-latest.js'


    with  open(outputDir+legacyjs,'w') as dlfile:
        dlfile.write(json.dumps(downloadDict,indent=4))

    with  open(outputDir+currentjs,'w') as dlfile:
        dlfile.write(json.dumps(downloadDict,indent=4))






def runTileDownloadProc(processIndex,tasksQueue,resultsQueue,localFilesPath,outputDir, baseurl, suffix,copylocal):
    kill_received = False
    while not kill_received:
        mapTile=None
        try:
            #this waits until new job is available
            mapTile = tasksQueue.get()
        except:
            #quit on Error
            kill_received=True

        if mapTile == None:
            #terminate on None job
            kill_received=True
        else:
            wasDownloaded, downloadSucceded, wasCopied, copySucceded = maptile_downloader(mapTile,localFilesPath,outputDir, baseurl, suffix,copylocal)
            resultsQueue.put([mapTile, processIndex, wasDownloaded, downloadSucceded , wasCopied, copySucceded])



def split_input_list(nSplit,mapList):

    subMapLists =[]
    lengthMapList = len(mapList)
    lengthSubMapList = np.int(np.floor(lengthMapList/nSplit))
    lengthFinSubMapList = lengthMapList - ((nSplit-1)*lengthSubMapList)

    for i in range(nSplit):
        if i != (nSplit-1):
            subMapList = mapList[i*lengthSubMapList:(i+1)*lengthSubMapList]
        else :
            subMapList = mapList[i*lengthSubMapList:]

        subMapLists.append(subMapList)

    return subMapLists



def download_list_top10nl():
    top10nlMapTiles = ['11HZ1', '11HZ2', '43BN1', '43BN2', '10HN2', '02GN2', '02GN1', '07BN1', '07BN2', '69AZ2', '69AZ1', '43FN1', '43FN2', '13CN1', '13CN2', '28AZ1', '28AZ2', '52BZ2', '29AN2', '29AN1', '52BZ1', '40HZ2', '40HZ1', '49GZ2', '49GZ1', '29CN1', '01HN1', '01HN2', '29CN2', '37AZ1', '37AZ2', '08CN1', '08CN2', '12HN1', '12HN2', '49FN2', '49FN1', '13AN2', '13AN1', '68CN2', '21CN1', '50EZ2', '50EZ1', '21CN2', '20FN2', '20FN1', '40CN1', '40CN2', '68EN1', '68EN2', '41EZ1', '41EZ2', '10HZ2', '21DZ2', '20BN2', '20BN1', '21DZ1', '41CZ2', '41CZ1', '10HZ1', '21FZ1', '21FZ2', '14BN1', '14BN2', '49CZ2', '49CZ1', '33EN1', '33EN2', '34DZ1', '34DZ2', '33CN2', '33CN1', '33AN1', '33AN2', '39FN1', '39FN2', '41DZ1', '39HN2', '39HN1', '46CN2', '46CN1', '07DN2', '07DN1', '65BN1', '65BN2', '14EZ2', '14EZ1', '37HN1', '46AN1', '46AN2', '37HN2', '07FN1', '07FN2', '34FZ2', '34FZ1', '14DN2', '14DN1', '70FZ2', '14FN1', '41FZ1', '57FZ1', '19CZ1', '57FZ2', '25DZ2', '25DZ1', '25FZ1', '25FZ2', '23AZ1', '23AZ2', '27EZ1', '27EZ2', '67AZ1', '02EZ2', '67AZ2', '40DN2', '40DN1', '15FZ2', '15FZ1', '45AZ1', '45AZ2', '40FN1', '40FN2', '45GZ2', '45GZ1', '11DZ1', '11DZ2', '24HZ1', '27DN1', '27DN2', '24HZ2', '67DN1', '67DN2', '38EZ1', '38EZ2', '04EZ2', '11BZ2', '11BZ1', '27CZ2', '27CZ1', '67BN2', '67BN1', '67GZ2', '67GZ1', '50AZ2', '50AZ1', '69BN1', '69BN2', '17GN1', '17GN2', '69DN2', '69DN1', '31FN1', '31FN2', '17AN2', '10EZ2', '10EZ1', '17AN1', '17CN1', '17CN2', '26CN1', '26CN2', '33FN2', '33FN1', '26EN2', '33DN2', '22GN1', '22GN2', '52HN1', '22AN2', '22AN1', '25HN2', '45HN1', '45HN2', '25HN1', '58BN1', '58BN2', '32AZ2', '32AZ1', '22CN1', '22CN2', '12EN1', '12EN2', '50DN2', '21BZ1', '21BZ2', '50DN1', '65EN2', '65EN1', '66FZ1', '66FZ2', '65GN1', '65GN2', '26AN2', '65AN2', '65AN1', '21HZ1', '34CN2', '11GZ2', '11GZ1', '11EZ1', '11EZ2', '49HN1', '49HN2', '10BZ2', '19DZ1', '19DZ2', '19BZ2', '19BZ1', '43GN1', '43GN2', '20DZ1', '20DZ2', '02FZ2', '02FZ1', '09EN1', '43EN2', '43EN1', '11HN1', '11HN2', '32GN1', '28GN2', '28GN1', '32GN2', '28EN1', '28EN2', '37GN2', '37GN1', '37EN1', '37EN2', '58HZ1', '28AN1', '28AN2', '68DN1', '68DN2', '52AN1', '52AN2', '49DZ1', '49DZ2', '37AN1', '37AN2', '40AZ2', '40AZ1', '40CZ1', '40CZ2', '57EN2', '57EN1', '68HN1', '31HZ2', '31HZ1', '57GN2', '68FN2', '68FN1', '15HN1', '15HN2', '20FZ2', '20FZ1', '38DN1', '38DN2', '32HN2', '32HN1', '33AZ1', '33AZ2', '17DN2', '17DN1', '44DN2', '44DN1', '17FN1', '32FN1', '32FN2', '17FN2', '44FN1', '44FN2', '33DZ1', '15BZ2', '46AZ1', '46AZ2', '33DZ2', '34FN2', '45BN2', '34FN1', '46DN1', '22DN2', '22DN1', '46DN2', '65BZ1', '65BZ2', '34DN1', '34DN2', '45BN1', '45BZ2', '45BZ1', '15CZ2', '34CN1', '15CZ1', '33CZ2', '33CZ1', '34BN2', '34BN1', '39BZ1', '39BZ2', '41FN1', '39DZ2', '39DZ1', '41DN1', '41DN2', '46CZ2', '46CZ1', '41BN2', '28BN2', '28BN1', '41BN1', '20AZ1', '44BZ2', '50FZ1', '50FZ2', '05GZ2', '05GZ1', '30EZ1', '30EZ2', '06GN2', '05HN1', '05HN2', '06GN1', '16GZ2', '16GZ1', '57BN1', '57BN2', '30FN2', '30FN1', '05FN2', '06BZ2', '06BZ1', '05FN1', '30DN2', '64DZ2', '67GN2', '67GN1', '27AN1', '27AN2', '27GN2', '27GN1', '67EN1', '67EN2', '06CN2', '06CN1', '64EN2', '06AN1', '06AN2', '23AN1', '23AN2', '58AN2', '58AN1', '67HZ1', '67HZ2', '38AN1', '38AN2', '38GN2', '38GN1', '39AZ2', '39AZ1', '43CZ1', '27HZ1', '27HZ2', '43CZ2', '27FZ2', '27FZ1', '39CZ1', '39CZ2', '24FN2', '67BZ2', '67BZ1', '24HN1', '27DZ1', '27DZ2', '24HN2', '27CN2', '27CN1', '17BZ1', '17BZ2', '32AN2', '32AN1', '19GZ2', '38HZ1', '38HZ2', '19GZ1', '31BZ1', '31BZ2', '32CN1', '58EN2', '58EN1', '32CN2', '32EN2', '32EN1', '19EZ1', '19EZ2', '58GN1', '31DZ2', '31DZ1', '58GN2', '26FZ1', '26FZ2', '26HZ2', '26HZ1', '01GZ2', '01GZ1', '12AZ1', '11EN1', '11EN2', '12AZ2', '50HZ2', '50HZ1', '11CN2', '12GZ2', '12GZ1', '11CN1', '03DN2', '03DN1', '10BN1', '10BN2', '18CZ1', '18CZ2', '44HZ2', '44HZ1', '10DN2', '10DN1', '11GN2', '11GN1', '10FN1', '10FN2', '15EZ1', '15EZ2', '20HN1', '20HN2', '33HN1', '51CN2', '20EZ2', '51CN1', '02DN1', '51BZ2', '51BZ1', '20DN2', '43GZ1', '43GZ2', '33HN2', '09AZ2', '09GZ2', '65CN1', '65HN2', '65HN1', '28HZ2', '69FN1', '06HZ1', '06HZ2', '69HN1', '30HZ1', '30HZ2', '49DN1', '49DN2', '33HZ2', '28DZ1', '28DZ2', '49BN2', '49BN1', '37BN2', '37BN1', '22FN1', '52EZ1', '52EZ2', '22FN2', '09HN2', '43DZ2', '52CZ2', '52CZ1', '43DZ1', '68DZ1', '68DZ2', '16HN1', '16HN2', '16FN2', '16FN1', '57EZ2', '57EZ1', '21BN1', '21BN2', '40BN1', '40BN2', '32DZ2', '32DZ1', '25AZ2', '25AZ1', '17FZ1', '32FZ1', '32FZ2', '17FZ2', '38FZ2', '21EZ2', '21EZ1', '38FZ1', '38DZ1', '38DZ2', '22BZ1', '22BZ2', '17HZ2', '17HZ1', '22FZ1', '10CN1', '22FZ2', '58CZ1', '58CZ2', '44BZ1', '10CN2', '68GZ2', '68GZ1', '44DZ2', '44DZ1', '07AN2', '07AN1', '26GN1', '26GN2', '33BN2', '33BN1', '34AZ1', '16CZ2', '16CZ1', '34AZ2', '51FZ2', '51FZ1', '50BN1', '50BN2', '28HZ1', '65CN2', '07EN2', '07EN1', '34GZ2', '34GZ1', '07GN1', '07GN2', '30DZ1', '30DZ2', '17EZ2', '17EZ1', '31AZ2', '31AZ1', '31CZ1', '31CZ2', '50FN1', '50FN2', '64GZ2', '64GZ1', '64EZ2', '44AZ2', '05DZ2', '44AZ1', '25EZ2', '25EZ1', '30FZ2', '64FN2', '64FN1', '30FZ1', '35AN2', '44CZ1', '44CZ2', '35AN1', '06GZ2', '05HZ1', '05HZ2', '06GZ1', '39CN1', '39CN2', '43AN2', '43AN1', '18BZ1', '39EN2', '39EN1', '43CN1', '27HN1', '27HN2', '43CN2', '12BZ2', '12BZ1', '16DZ1', '16DZ2', '02CZ2', '02CZ1', '18HZ2', '51AZ1', '21HN2', '58GZ1', '04DZ2', '43BZ2', '58GZ2', '19GN2', '38HN1', '38HN2', '19GN1', '58AZ2', '58AZ1', '39AN2', '39AN1', '13BN1', '69AN2', '69AN1', '13BN2', '13DN2', '13DN1', '69CN2', '69EN2', '69EN1', '17BN1', '17BN2', '26BN1', '29AZ2', '29AZ1', '26BN2', '26DN2', '26DN1', '49GN2', '49GN1', '08DN2', '08DN1', '49EN1', '37DZ2', '50GN1', '50GN2', '68BN2', '68BN1', '07HZ2', '09BZ2', '09BZ1', '68CZ2', '58DZ2', '58DZ1', '50EN2', '50EN1', '66HN2', '66HN1', '55EN1', '55EN2', '52DZ1', '52DZ2', '55CN1', '55AN1', '55AN2', '21DN2', '21DN1', '51HN1', '51HN2', '21FN1', '21FN2', '52FZ1', '14AN2', '28FN2', '28FN1', '28DN1', '46BN2', '46BN1', '28DN2', '41AZ1', '41AZ2', '49AZ1', '49AZ2', '49EZ1', '07CZ1', '07CZ2', '37HZ1', '37DN2', '51AZ2', '19HZ1', '14EN2', '14EN1', '14HZ1', '36HN2', '19HZ2', '14GN1', '14GN2', '22EZ2', '22EZ1', '43BZ1', '43HN2', '43HN1', '57FN1', '57FN2', '28CZ2', '28CZ1', '16HZ1', '16HZ2', '27EN1', '27EN2', '67CN2', '67CN1', '40FZ1', '40FZ2', '67AN1', '67AN2', '37CZ2', '06EN1', '06EN2', '37CZ1', '38EN1', '10BZ1', '38EN2', '58BZ1', '58BZ2', '45EZ1', '45EZ2', '17AZ2', '17AZ1', '25BZ1', '25BZ2', '58CN1', '17CZ1', '17CZ2', '58CN2', '22BN1', '22BN2', '07GZ1', '52HZ1', '07GZ2', '03CZ1', '03CZ2', '34GN2', '34GN1', '22AZ2', '45CZ2', '45CZ1', '22AZ1', '07AZ2', '07AZ1', '26EZ2', '14HN2', '15BZ1', '26EZ1', '34EN1', '34EN2', '22CZ1', '22CZ2', '26GZ1', '26GZ2', '14HN1', '33BZ2', '33BZ1', '10GZ1', '11AN1', '11AN2', '10GZ2', '31AN2', '11FZ2', '11FZ1', '31AN1', '65GZ1', '65GZ2', '65AZ2', '65AZ1', '44AN2', '24FZ2', '05DN2', '44AN1', '05BN1', '12FN2', '12FN1', '16DN1', '16DN2', '16BN2', '16BN1', '51GN2', '51GN1', '31DN2', '51EN1', '51EN2', '18BN1', '31DN1', '12BN2', '12BN1', '69EZ2', '69EZ1', '03HZ2', '03HZ1', '55BZ1', '51AN1', '51AN2', '28GZ2', '28GZ1', '37FN2', '37FN1', '28EZ1', '28EZ2', '37DN1', '49EZ2', '07HN2', '07HN1', '19FZ2', '19FZ1', '04GZ1', '57HZ2', '57HZ1', '37GZ2', '37GZ1', '37EZ1', '37EZ2', '09BN2', '09BN1', '14CZ1', '14CZ2', '08DZ2', '08DZ1', '03GN1', '50GZ2', '55AZ1', '55AZ2', '40HN2', '40HN1', '50GZ1', '37DZ1', '03GN2', '49EN2', '31HN2', '31HN1', '52FN1', '49FZ2', '49FZ1', '52DN1', '52DN2', '15HZ1', '15HZ2', '52BN2', '52BN1', '08AZ2', '08AZ1', '08CZ1', '08CZ2', '15GN2', '34BZ2', '34BZ1', '40GZ1', '40GZ2', '03GZ1', '45FN2', '45FN1', '03GZ2', '45DN1', '45DN2', '20GN2', '20GN1', '41BZ2', '41BZ1', '14GZ1', '14GZ2', '56FN2', '41GN2', '41GN1', '14AZ2', '46DZ1', '20BZ2', '20BZ1', '46DZ2', '41EN1', '38CN2', '41CN2', '41CN1', '38CN1', '40EZ2', '46BZ2', '46BZ1', '40EZ1', '49CN2', '49CN1', '07CN1', '20AN1', '20AN2', '07CN2', '49AN1', '49AN2', '06FN2', '06FN1', '64HN1', '64HN2', '05GN2', '05GN1', '30GN2', '30GN1', '30EN2', '39FZ1', '65FZ1', '65FZ2', '39FZ2', '39HZ2', '39HZ1', '16GN2', '16GN1', '64DN2', '16EN1', '33GZ1', '57BZ1', '57BZ2', '07DZ2', '06BN2', '06BN1', '07DZ1', '33EZ1', '33EZ2', '07FZ1', '07FZ2', '27AZ1', '27AZ2', '39GN1', '39GN2', '27GZ2', '27GZ1', '46GZ2', '46GZ1', '67EZ1', '67EZ2', '14DZ2', '14DZ1', '46EZ1', '65DZ2', '14FZ1', '14FZ2', '65DZ1', '38AZ1', '38AZ2', '19EN1', '19EN2', '38GZ2', '38GZ1', '38CZ2', '25BN1', '25BN2', '19CN2', '38CZ1', '19CN1', '25DN2', '19AN1', '19AN2', '25DN1', '25FN1', '25FN2', '45CN2', '45CN1', '45AN1', '45AN2', '32CZ1', '32CZ2', '32EZ2', '32EZ1', '26FN1', '26FN2', '32GZ1', '11DN1', '11DN2', '11BN2', '11BN1', '26HN2', '26HN1', '32GZ2', '50AN2', '50AN1', '31FZ1', '31FZ2', '50CN1', '50CN2', '27BZ2', '69BZ1', '69BZ2', '27BZ1', '03DZ2', '03DZ1', '67FZ2', '67FZ1', '11CZ2', '10EN2', '10EN1', '11CZ1', '10GN1', '11AZ1', '11AZ2', '10GN2', '11FN2', '11FN1', '10DZ2', '44HN2', '44HN1', '10FZ1', '10FZ2', '45HZ1', '45HZ2', '02HZ1', '40GN1', '12EZ1', '12EZ2', '66FN1', '66FN2', '01CZ2', '01CZ1', '20HZ1', '20HZ2', '33DN1', '02DZ1', '02DZ2', '26EN1', '12CZ2', '12CZ1', '09DN1', '50DZ2', '51BN2', '51BN1', '50DZ1', '19FN2', '19FN1', '69GN1', '69GN2', '19DN1', '19DN2', '04GN1', '04GN2', '34HN1', '34HN2', '03HN2', '03HN1', '18AZ2', '18AZ1', '65HZ2', '65HZ1', '07BZ1', '07BZ2', '41HN1', '69FZ1', '19HN1', '30HN1', '30HN2', '07HZ1', '43DN2', '14BZ1', '14BZ2', '43DN1', '09EZ1', '49BZ2', '49BZ1', '14HZ2', '43EZ2', '43EZ1', '14CN2', '09CZ2', '31EZ1', '06DZ1', '06DZ2', '21AN2', '21AN1', '55BN1', '08AN1', '52AZ1', '52AZ2', '45DZ1', '45DZ2', '68GN2', '68GN1', '25AN2', '25AN1', '25CN1', '25CN2', '68HZ1', '21EN2', '21EN1', '52GZ2', '52GZ1', '21GN1', '21GN2', '40EN2', '40EN1', '21HZ2', '40GN2', '57AZ2', '57AZ1', '45FZ2', '45FZ1', '40AN2', '40AN1', '15GZ2', '34AN1', '34AN2', '17DZ2', '17DZ1', '20GZ2', '20GZ1', '31CN1', '31CN2', '32BZ1', '32BZ2', '50BZ1', '50BZ2', '44FZ1', '44FZ2', '05EZ2', '31EN2', '31EN1', '38BZ2', '31GN1', '31GN2', '32HZ2', '32HZ1', '38BZ1', '16AZ1', '16AZ2', '44CN1', '44CN2', '35AZ1', '22DZ2', '22DZ1', '16EZ1', '16EZ2', '44EN2', '44EN1', '06FZ2', '06FZ1', '17EN2', '17EN1', '44GN1', '44GN2', '64HZ1', '64HZ2', '30GZ2', '30GZ1', '12DN1', '12DN2', '39BN1', '39BN2', '65DN2', '39DN2', '39DN1', '65DN1', '46GN2', '46GN1', '65FN1', '65FN2', '28BZ2', '28BZ1', '64FZ2', '64FZ1', '19AZ1', '19AZ2', '43AZ2', '43AZ1', '51DZ1', '51DZ2', '39EZ2', '39EZ1', '39GZ1', '39GZ2', '25GZ1', '25GZ2', '05FZ2', '04DN2', '05FZ1', '41EN2', '04FN2', '26AZ2', '19CZ2', '10HN1', '21HN1', '13BZ1', '13BZ2', '13DZ2', '13DZ1', '06CZ2', '06CZ1', '06AZ1', '06AZ2', '26BZ1', '26BZ2', '36FZ2', '65CZ1', '02HZ2', '33GN2', '27FN2', '26DZ2', '26DZ1', '27FN1', '67FN2', '67FN1', '02GZ2', '02GZ1', '33GN1', '02EZ1', '09DN2', '43FZ1', '43FZ2', '68BZ2', '68BZ1', '31BN1', '31BN2', '58EZ2', '58EZ1', '27BN2', '27BN1', '67HN1', '67HN2', '01GN2', '01GN1', '58DN2', '58DN1', '58FN1', '05AN1', '05AN2', '12AN1', '12AN2', '12GN2', '12GN1', '13AZ2', '13AZ1', '29CZ1', '01HZ1', '01HZ2', '29CZ2', '13CZ1', '13CZ2', '02HN1', '01DZ1', '01DZ2', '02HN2', '21CZ1', '18AN2', '18AN1', '21CZ2', '51HZ1', '51HZ2', '12HZ1', '12HZ2', '18CN1', '18CN2', '50HN2', '50HN1', '12CN2', '12CN1', '68EZ1', '68EZ2', '28FZ2', '28FZ1', '41AN1', '41AN2', '15EN1', '15EN2', '09CN2', '43HZ2', '43HZ1', '51CZ2', '20EN2', '51CZ1', '28CN2', '28CN1', '06HN1', '06HN2', '22EN2', '22EN1', '37CN2', '06EZ1', '06EZ2', '37CN1', '06DN1', '37BZ2', '37BZ1', '06DN2', '65CZ2', '21GZ1', '21GZ2', '25CZ1', '25CZ2', '52GN2', '52GN1', '31EZ2', '21AZ2', '21AZ1', '52EN1', '52EN2', '52CN2', '52CN1', '09HZ1', '09HZ2', '37HZ2', '16FZ2', '16FZ1', '57AN2', '57AN1', '15FN2', '15FN1', '45GN2', '45GN1', '45EN1', '45EN2', '40BZ1', '40BZ2', '31GZ1', '31GZ2', '38FN2', '38FN1', '34EZ1', '34EZ2', '15BN2', '15BN1', '34CZ2', '34CZ1', '40DZ2', '40DZ1', '44GZ1', '44GZ2', '17HN2', '17HN1', '44BN1', '44BN2', '32BN1', '32BN2', '38BN2', '38BN1', '32DN2', '32DN1', '33GZ2', '25HZ2', '25HZ1', '17GZ1', '17GZ2', '16CN2', '16CN1', '16EN2', '44EZ2', '44EZ1', '16AN1', '16AN2', '51FN2', '51FN1', '03AZ1', '51DN1', '51DN2', '33HZ1', '26AZ1', '16BZ2', '33FZ2', '33FZ1', '16BZ1', '22GZ1', '12FZ2', '07EZ2', '07EZ1', '12FZ1', '28HN1', '26CZ1', '26CZ2', '28HN2', '12DZ1', '12DZ2', '51GZ2', '51GZ1', '10AZ2', '51EZ2', '04FZ1', '04FZ2', '65EZ2', '65EZ1', '51EZ1', '19BN2', '19BN1', '25EN2', '25EN1', '25GN1', '25GN2', '09DZ1', '09DZ2', '37FZ2', '37FZ1', '02CN2', '02CN1', '57HN2', '57HN1', '64GN2', '64GN1']

    return top10nlMapTiles


def main():
    args = argument_parser().parse_args()
    print('local repository: ', args.localrepository)
    print('output directory/download destination : ',args.outputdirectory)
    print('base url : ',args.baseurl)
    print('file suffix : ' args.suffix)
    print('running {} processes'.format(args.proc))
    print('copying from local repository: {}'.format(args.copylocal))
    print('run tag is {}'.format(args.tag))
    if args.inputlist != None:
        print('{} specified as input list'.format(args.inputlist))


    
    if args.inputlist != None:
        allMapTiles = read_input(args.inputlist)
    else:
        allMapTiles = download_list_top10nl()


    if len(allMapTiles) == 0:
        print('no tiles specified. aborting')
    else:
        
        try:
            t0 = time.time()
            print('starting ...')
            if args.copylocal == 'False':
                copylocal_val = False
            elif args.copylocal == 'True':
                copylocal_val = True
            else :
                print('no value for copylocal set')

            run(args.localrepository, args.outputdirectory, args.baseurl, args.suffix, args.proc, args.tag, inputList=allMapTiles,copylocal=copylocal_val)
            print('finished in {} seconds'.format(time.time() - t0))

        except:
            print('Execution failed.')
            print(traceback.format_exc())






if __name__ == "__main__":
    main()
