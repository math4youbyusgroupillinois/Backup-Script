import os
from Tkinter import *
import paramiko
from scp import SCPClient
port = 22
info = {}

def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def pull(paths):
    try:
        name = paths[0]
        path = paths[1]
        pathDir = path.replace("/","_").replace(".","_")
        ssh = createSSHClient(info[name]["ip"], port, info[name]["username"], info[name]["password"])
        scp = SCPClient(ssh.get_transport())
        folders = [x[1] for x in os.walk("{}/{}".format(name,pathDir))][0]
        folderSize = len(folders)
        os.makedirs("{}/{}/{}".format(name,pathDir,folderSize))
        ssh.exec_command("find "+path+" -type f -exec md5sum {} \; > hashes.txt")[1].read()
        scp.get("hashes.txt","{}/{}/{}".format(name,pathDir,folderSize))
        ssh.exec_command("rm hashes.txt")[1].read()    
        ssh.exec_command("tar -zcvf {}.tar.gz {}".format(folderSize,path))[1].read()
        scp.get("{}.tar.gz".format(folderSize),"{}/{}/{}".format(name,pathDir,folderSize))
        ssh.exec_command("md5sum {}.tar.gz > compressionHash.txt".format(folderSize))[1].read()
        ssh.exec_command("rm {}.tar.gz".format(folderSize))[1].read()
        scp.get("compressionHash.txt","{}/{}/{}".format(name,pathDir,folderSize))
        ssh.exec_command("rm compressionHash.txt")[1].read()
        ssh.close()
    except:
        try:
            ssh.close()
        except:
            pass
        print "Error"
    
def push(paths):
    try:
        name = paths[0]
        path = paths[1]
        name = paths[0]
        path = paths[1]
        pathDir = path.replace("/","_").replace(".","_")
        ssh = createSSHClient(info[name]["ip"], port, info[name]["username"], info[name]["password"])
        scp = SCPClient(ssh.get_transport())
        folders = [x[1] for x in os.walk("{}/{}".format(name,pathDir))][0]
        folderSize = len(folders)
        scp.put("{}/{}/{}/{}.tar.gz".format(name,pathDir,folderSize-1,folderSize-1),"/tmp/backup.tar.gz")
        ssh.close()
    except:
        try:
            ssh.close()
        except:
            pass
        print "Error"

def compare(paths):
    try:
        name = paths[0]
        path = paths[1]
        pathDir = path.replace("/","_").replace(".","_")
        ssh = createSSHClient(info[name]["ip"], port, info[name]["username"], info[name]["password"])
        folders = [x[1] for x in os.walk("{}/{}".format(name,pathDir))][0]
        folderSize = len(folders)
        localHashes = open("{}/{}/{}/hashes.txt".format(name,pathDir,folderSize-1),"r").read()
        remoteHashes = ssh.exec_command("find "+path+" -type f -exec md5sum {} \;")[1].read()
        ssh.close()
        localHashes = localHashes.split("\n")
        localHashes = localHashes[:len(localHashes)-1]
        remoteHashes = remoteHashes.split("\n")
        remoteHashes = remoteHashes[:len(remoteHashes)-1]
        localDic = {}
        remoteDic = {}
        for i in localHashes:
            temp = i.split()
            localDic.update({temp[1]:temp[0]})
        for i in remoteHashes:
            temp = i.split()
            remoteDic.update({temp[1]:temp[0]})
        changed = []
        missing = []
        new = []
        for localFile in localDic.keys():
            try:
                if localDic[localFile] != remoteDic[localFile]:
                    changed.append(localFile)
                remoteDic.pop(localFile)
            except:
                missing.append(localFile)
        new = remoteDic.keys()
        print("")
        print "-"*(len(name)+len(path)+2)
        print "{}({})".format(name,path)
        print "-"*(len(name)+len(path)+2)  
        print "CHANGED:"
        if changed == []:
            print "\tNone"
        else:
            for i in changed:
                print "\t{}".format(i)
        print("")
        print "MISSING:"
        if missing == []:
            print "\tNone"
        else:
            for i in missing:
                print "\t{}".format(i)
        print("")
        print "NEW:"
        if new == []:
            print "\tNone"
        else:
            for i in new:
                print "\t{}".format(i)
        print("")        
    except:
        try:
            ssh.close()
        except:
            pass
        print "Error"

def controlPanel():
    window = Tk()
    window.title("Control Panel")
    count = 0
    Label(window, text = "----------------------").grid(row=count,column=0)
    Label(window, text = "----------------------").grid(row=count,column=1)
    Label(window, text = "----------------------").grid(row=count,column=2)
    count += 1
    for directory in info.keys():
        Label(window, text = directory).grid(row=count,column=1,pady=5)
        count += 1
        for subdirectory in info[directory]["backup"]:
            Label(window, text = subdirectory).grid(row=count,column=0)
            count += 1
            items = [directory,subdirectory]
            Button(window, text = "PULL", width = 10, command = lambda paths=items:pull(paths)).grid(row=count,column=0,padx=5,pady=5)
            Button(window, text = "PUSH", width = 10, command = lambda paths=items:push(paths)).grid(row=count,column=1,padx=5,pady=5)
            Button(window, text = "COMPARE", width = 10, command = lambda paths=items:compare(paths)).grid(row=count,column=2,padx=5,pady=5)
            count += 1
        Label(window, text = "----------------------").grid(row=count,column=0)
        Label(window, text = "----------------------").grid(row=count,column=1)
        Label(window, text = "----------------------").grid(row=count,column=2)
        count += 1
    return window

def createDirectories():
    for directory in info.keys():
        if not os.path.exists(directory):
            os.makedirs(directory)
        for subdirectory in info[directory]["backup"]:
            if not os.path.exists("{}/{}".format(directory,subdirectory.replace("/","_").replace(".","_"))):
                os.makedirs("{}/{}".format(directory,subdirectory.replace("/","_").replace(".","_")))

def getInfo():
    fileName = raw_input("File: ")
    fileObject = open(fileName,"r")
    fileContent = fileObject.read()
    fileObject.close()
    fileContent = fileContent.split("\n")
    for i in range(len(fileContent)):
        fileContent[i] = fileContent[i].split()
    for line in fileContent:
        temp = {}
        temp.update({"ip":line[1]})
        temp.update({"username":line[2]})
        temp.update({"password":line[3]})
        temp.update({"backup":line[4:]})
        info.update({line[0]:temp})
    
def main():
    getInfo()
    createDirectories()
    CP = controlPanel()
    CP.mainloop()

if __name__ == '__main__':
    main()
