import json
import os
import sys


class InputReader:
    def __init__(self, inInputFileName: str):
        if os.path.exists(inInputFileName):
            with open(inInputFileName) as file:
                inInputFile = json.load(file)
        else:
            print(f"Error: Given {inInputFileName} file not found")
            sys.exit(1)
        self.mRemoteMachineAddress = inInputFile['RemoteMachineAddress']
        self.mPathInfo = dict()
        for packageName, pathInfo in inInputFile['Source'].items():
            self.mPathInfo[packageName] = list()
            for path in pathInfo:
                if os.path.exists(path['SourcePath']):
                    self.mPathInfo[packageName].append({
                        "SourcePath": path['SourcePath'],
                        "DestPath": path['DestPath'],
                        "SetupMethod": path['SetupMethod'] if 'SetupMethod' in path else '',
                        "ForceUpdate": path['ForceUpdate'] if 'ForceUpdate' in path else False,
                        "Branch": path['Branch'] if 'Branch' in path else None,
                        "Brand": path['Brand'] if 'Brand' in path else None
                    })
