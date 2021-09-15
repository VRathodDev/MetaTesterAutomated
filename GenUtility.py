"""
General Utility Functions
"""

import errno
import os
import subprocess
from enum import IntEnum


class TimeOutLevel(IntEnum):

    LOW = 300
    MEDIUM = 600
    HIGH = 1200


def isNoneOrEmpty(*args) -> bool:
    """Checks if any of the given argument is None or Empty."""
    return any(map(lambda inArgs: inArgs is None or len(inArgs) == 0, args))


def createDir(inDirPath: str, inMode: int = 0o777):
    """Creates the absent directories from the given path."""
    try:
        os.makedirs(inDirPath, inMode)
    except OSError as err:
        # Re-raise the error unless it's for already existing directory
        if err.errno != errno.EEXIST or not os.path.isdir(inDirPath):
            raise


def writeInFile(inFileContent: str, inFileLocation: str):
    """Writes the content in the provided file location"""
    if not isNoneOrEmpty(inFileContent, inFileLocation):
        targetLocation = os.path.abspath(inFileLocation)
        fileName = targetLocation.split(os.sep)[-1]
        targetDir = targetLocation[:targetLocation.index(fileName)]
        if fileName.find('.') <= 0:
            print(f"Error: `{inFileLocation}` must contain File Name with valid File Extension. "
                  f"i.e `Z:fakepath/file_name.txt")
            return False
        if not os.path.exists(targetDir):
            createDir(targetDir)
        with open(inFileLocation, 'w') as file:
            file.write(inFileContent)
        return True
    else:
        print('Error: Invalid Parameters')
        return False


def runExecutable(inCommands: str, inTimeOut: TimeOutLevel = TimeOutLevel.MEDIUM):
    """Opens up an executable file."""
    if not isNoneOrEmpty(inCommands):
        with open('exec.bat', 'w') as file:
            file.write(inCommands)
        try:
            subprocess.run('exec.bat', timeout=inTimeOut.value)
        except subprocess.TimeoutExpired:
            print(f"Error: {inCommands} could not be executed in {inTimeOut.value/60} Minutes!")
            return False
        finally:
            os.remove('exec.bat')
        return True
    else:
        return False
