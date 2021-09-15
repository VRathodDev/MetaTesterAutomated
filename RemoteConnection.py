import win32wnet
from GenUtility import isNoneOrEmpty


class RemoteConnection:
    def __init__(self, in_HostAddress: str, in_UserName: str, in_Password):
        self.__mHostAddress = in_HostAddress
        self.__mUserName = in_UserName
        self.__mPassword = in_Password

    def connect(self):
        """
        Connects to the given host via provided credentials \n
        :return: Returns True if successfully connected else False
        """
        if not isNoneOrEmpty(self.__mHostAddress, self.__mUserName, self.__mPassword):
            unc = ''.join(['\\\\', self.__mHostAddress])
            netResource = win32wnet.NETRESOURCE()
            netResource.lpRemoteName = unc
            try:
                win32wnet.WNetAddConnection2(netResource, self.__mPassword, self.__mUserName, 0)
            except Exception as error:
                if isinstance(error, win32wnet.error):
                    if 1219 in error.args:
                        # Disconnects from existing connection if any & tried to connect again
                        win32wnet.WNetCancelConnection2(unc, 0, 0)
                        return self.connect()
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
        Disconnects from the given host \n
        :return: Returns True if successfully disconnected else False
        """
        unc = ''.join(['\\\\', self.__mHostAddress])
        try:
            win32wnet.WNetCancelConnection2(unc, 0, 0)
        except Exception as error:
            print(f"Error: {error}")
            return False
        return True
