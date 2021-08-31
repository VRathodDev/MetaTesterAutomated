import os
import os.path
import shutil
import sys
import win32wnet


class RemoteConnection:
    def __init__(self, in_HostAddress: str, in_UserName: str, in_Password):
        self.mHostAddress = in_HostAddress
        self.mUserName = in_UserName
        self.mPassword = in_Password

    def connect(self):
        """
        Connects to the given host via provided credentials
        :return: Returns True if successfully connected else False
        """
        if all(map(lambda x: x is not None and len(x) > 0, [self.mHostAddress, self.mUserName, self.mPassword])):
            unc = ''.join(['\\\\', self.mHostAddress])
            netResource = win32wnet.NETRESOURCE()
            netResource.lpRemoteName = unc
            try:
                win32wnet.WNetAddConnection2(netResource, self.mPassword, self.mUserName, 0)
            except Exception as error:
                if isinstance(error, win32wnet.error):
                    if 1219 in error.args:
                        win32wnet.WNetCancelConnection2(unc, 0, 0)
                        return RemoteConnection.connect(self.mHostAddress, self.mUserName, self.mPassword)
                    elif 1326 in error.args:
                        print('Error: Invalid Username or Password!')
                        return False
                    else:
                        print(f"Error: {error}")
                        return False
                else:
                    print(f"Error: {error}")
                    return False
            return True
        else:
            print('Error: Invalid Input Parameters!')
            return False

    def disconnect(self):
        """
        Disconnects from the given host
        :return: Returns True if successfully disconnected else False
        """
        unc = ''.join(['\\\\', self.mHostAddress])
        try:
            win32wnet.WNetCancelConnection2(unc, 0, 0)
        except Exception as error:
            print(f"Error: {error}")
            return False
        return True
