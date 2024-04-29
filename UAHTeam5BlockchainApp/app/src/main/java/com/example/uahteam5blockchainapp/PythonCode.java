package com.example.uahteam5blockchainapp;

import android.content.Context;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;

import androidx.navigation.fragment.NavHostFragment;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class PythonCode
{
    //String variable to hold the current user
    private String currentUser;

    //Private boolean variable to hold if the user is logged in or not
    private boolean isLoggedIn;

    //Declares a singleton variable for the class
    private static PythonCode currentInstance = null;

    //Private python variable to run the code
    private PyObject pythonModule;
    private PyObject blockchain;
    private String targetIP;
    private String currentRole;
    private PyObject privateKey;
    private PyObject publicKey;
    private PyObject fileKey;

    //Private constructor for the class
    private PythonCode(Context context)
    {
        //If the python code is not running, then start it
        if (!Python.isStarted())
        {
            //Starts the python code
            Python.start(new AndroidPlatform(context));
        }
        //Gets the current instance of Python running
        Python pythonCode = Python.getInstance();
        //Gets the module "lightweight" from the src/main/python directory
        pythonModule = pythonCode.getModule("lightweight");
    }

    //Singleton constructor for the class
    public static PythonCode PythonCode(Context context)
    {
        //If no class has been defined previously, then make a new class
        if (currentInstance == null)
        {
            //Makes a new class for the current class
            currentInstance = new PythonCode(context);
        }
        return currentInstance;     //Returns the new instance of the singleton class
    }

    //Function to login with the given credentials
    public boolean login(String userName, String password)
    {
        //If the blockchain is null, return false to show that the user has not and cannot login
        if (blockchain == null)
        {
            return false;
        }
        //If the variable is a blockchain, i.e. a list, then login

        if (pythonModule.callAttr("isBlockchain", blockchain).toJava(boolean.class))
        {
            //Log.e("Result", blockchain.toJava(String.class));
            currentUser = userName;
            //Calls the login() function in Python and sends it the login arguments and returns the result
            PyObject result = pythonModule.callAttr("login", userName, password, blockchain);
            //Converts the PyObject to a Java boolean instance and examines it for successfulness in logging in
            return result.toJava(boolean.class);
        }
        //Else, the blockchain is a string, so return false as it cannot be processed
        else
        {
            return false;
        }
    }

    //Function to upload the given file
    public String uploadFile(byte[] fileContentToUpload, String filePath, String fileName, String array)
    {
        //Log.e("bytes", Arrays.toString(fileContentToUpload));
        //Calls the uploadIpfs() function in Python and sends it the login arguments and returns the result
        String result = pythonModule.callAttr("uploadIpfs", fileKey, currentUser, fileName, blockchain, fileContentToUpload, fileName, targetIP, array, filePath).toJava(String.class);
        Log.e("result", result);
        return result;
    }

    //Function to download the requested file from the blockchain
    public boolean downloadFile(String fileHash, String filePath, String fileName)
    {
        //Calls the retrieveIpfs() function in Python downloads the file
        PyObject result = pythonModule.callAttr("retrieveIpfs", fileKey, blockchain, fileName, fileHash, currentUser, targetIP, filePath);
        //Log.e("resultingboolean", result.toJava(boolean.class).toString());
        return result.toJava(boolean.class);
        /*
        //Tries to write the data to an output file in the download file directory
        try
        {
            //Creates a new file writer for the given path
            FileOutputStream fileOutputStream = new FileOutputStream(filePath);
            //Converts the content to bytes and writes the result to the file writer
            fileOutputStream.write(resultingData);
            //Closes the file writer
            fileOutputStream.close();
            //Opens the file and reads it bytes
            try
            {
                byte[] uploadBytes = getUploadBytes(filePath);

                //Calls the function to decrypt the written file contents
                PyObject newresult = pythonModule.callAttr("decryptFile", uploadBytes);

                byte[] newresultingData = newresult.toJava(byte[].class);
                //Tries to write the data to an output file in the download file directory
                try
                {
                    //Creates a new file writer for the given path
                    FileOutputStream newfileOutputStream = new FileOutputStream(filePath);
                    //Converts the content to bytes and writes the result to the file writer
                    fileOutputStream.write(newresultingData);
                    //Closes the file writer
                    fileOutputStream.close();

                }
                //Catches an IO Exception
                catch (IOException error)
                {
                    //Should not happen. But, if it does, log it
                    Log.e("File Decryption error", "Cannot decrypt'" + filePath + "' from the computer");
                    return false;       //Returns false to show that the download did not work
                }
            }
            //Catches an input exception
            catch (Exception error)
            {
                Log.e("IOerrorMessage", Arrays.toString(error.getStackTrace()));
            }
        }
        //Catches an IO Exception
        catch (IOException error)
        {
            //Should not happen. But, if it does, log it
            Log.e("File Download error", "Cannot download'" + filePath + "' from the blockchain");
            return false;       //Returns false to show that the download did not work
        }
        return true;        //Returns true to show that the operation was a success

         */
    }

    //Function to start the local blockchain
    public void start()
    {
        //Calls the main() function in Python to get the most recent blockchain
        //blockchain = pythonModule.callAttr("main", targetIP);
    }

    //Function to download the list of available files
    public ArrayList<String> listFiles()
    {
        //Calls the getFileList() function in Python and sends it the blockchain and returns the result
        PyObject result = pythonModule.callAttr("getFileList", blockchain);
        //Creates a new ArrayList to contain the result
        ArrayList<String> listOfFileNames = new ArrayList<>();
        //Converts the result from Python list to a list of Python
        List<PyObject> listConversion = result.asList();
        //Loops through all items in the list and returns them as a list
        for (int i = 0; i < listConversion.size(); i++)
        {
            listOfFileNames.add(listConversion.get(i).toString());      //Adds the current element to the new list
        }
        //Converts the PyObject to a Java ArrayList<String> instance and returns it to the calling function
        return listOfFileNames;
    }

    //Function to download the list of file hashes
    public ArrayList<String> listHashes()
    {
        //Calls the getipfsHashes() function in Python and sends it the blockchain and returns the result
        PyObject result = pythonModule.callAttr("getipfsHashes", blockchain);
        //Creates a new ArrayList to contain the result
        ArrayList<String> listOfFileHashes = new ArrayList<>();
        //Converts the result from Python list to a list of Python
        List<PyObject> listConversion = result.asList();
        //Loops through all items in the list and returns them as a list
        for (int i = 0; i < listConversion.size(); i++)
        {
            listOfFileHashes.add(listConversion.get(i).toString());      //Adds the current element to the new list
        }
        //Converts the PyObject to a Java ArrayList<String> instance and returns it to the calling function
        return listOfFileHashes;
    }

    //Function to refresh the blockchain
    public void refreshBlockchain()
    {
        //Calls the refreshBlockchain() function in Python and saves the returned blockchain
        blockchain = pythonModule.callAttr("refreshBlockchain", targetIP);
        //Ensures the app will not crash with empty blockchain data
        //if (blockchain.equals("DeviceNotOnline"))
        //{
        //    blockchain = null;
        //}
    }

    //Function to create a new user account
    //Might have an issue with the blockchain and may need to ensure the local blockchain is updated and synchronized before logging in
    public boolean createUser(String Fullname, String Username, String Password, String role)
    {
        //Calls the createAccount() function in Python and returns the status of the account creation
        PyObject result = pythonModule.callAttr("createNewAccount", Username, Password, role, Fullname, blockchain, targetIP, currentUser);
        //If the result was a string, return true for success
        if (result.toJava(String.class).equals("True"))
        {
            return true;
        }
        //Else, return false to show the account was NOT created
        return false;
    }

    //Function to get the user's role from the blockchain
    public String getUserRole(String username)
    {
        //Calls the getUserRole() function in Python and returns the resulting String
        PyObject result = pythonModule.callAttr("getUserRole", blockchain, username);
        //Converts the PyObject to a Java String instance and returns it to the calling function
        return result.toJava(String.class);
    }

    //Function to get the list of active users from the blockchain
    //Requires more work
    public ArrayList<String> getListActiveUsers()
    {
        //Calls the getListActiveUsers() function in Python and sends it the blockchain and returns the result
        PyObject result = pythonModule.callAttr("getListActiveUsers", blockchain);
        //Creates a new ArrayList to contain the result
        ArrayList<String> listOfActiveUsers = new ArrayList<>();
        //Converts the result from Python list to a list of Python
        List<PyObject> listConversion = result.asList();
        //Loops through all items in the list and returns them as a list
        for (int i = 0; i < listConversion.size(); i++)
        {
            listOfActiveUsers.add(listConversion.get(i).toString());      //Adds the current element to the new list
        }
        //If it is present, removes the current user from the list of active users
        listOfActiveUsers.remove(currentUser);
        //Converts the PyObject to a Java ArrayList<String> instance and returns it to the calling function
        return listOfActiveUsers;
    }

    //Function to get the blockchain as viewable text
    public String getCurrentBlockchain()
    {
        //Calls the python code to get the string version of the blockchain
        //Calls the getTextBlockchain() function in Python and returns the resulting String
        PyObject result = pythonModule.callAttr("getTextBlockchain", blockchain);
        //Converts the PyObject to a Java String instance and returns it to the calling function
        return result.toJava(String.class);
    }

    //Function to set the login status of the user
    public void setLoggedIn(boolean loggedIn)
    {
        isLoggedIn = loggedIn;
        //Calls the setLoggedInStatus() function in Python to log in or out the user
        //pythonModule.callAttr("setLoggedInStatus", loggedIn);
        //If the user is logging out, make the keys null for security
        if (!loggedIn)
        {
            publicKey = null;
            privateKey = null;
            fileKey = null;
        }
    }

    //Function to set the target IP in the code
    public void setTargetIP(String newIPAddress)
    {
        targetIP = newIPAddress;
        //Calls the setLoggedInStatus() function in Python to log in or out the user
        //pythonModule.callAttr("setTargetIP", newIPAddress);
    }

    //Function to get the login status of the user
    public boolean isLoggedIn()
    {
        return isLoggedIn;
    }

    //Function to set the current role
    public void setCurrentRole(String newRole)
    {
        currentRole = newRole;
    }

    //Function to get the current role
    public String getCurrentRole()
    {
        return currentRole;
    }

    //Function to get the currently logged in user
    public String getCurrentUser()
    {
        return  currentUser;
    }

    //Function to get the encryption key from the python code
    //Should only be called once upon successful login
    public void getEncryptionKeys()
    {
        //Calls the getKeys() function in Python and saves the returned PyObject
        PyObject result = pythonModule.callAttr("genKeys");
        //Calls the python code to parse result into a publicKey and a privateKey
        publicKey = pythonModule.callAttr("getPublicKey", result);
        privateKey = pythonModule.callAttr("getPrivateKey", result);
        //Calls the python module to get the symmetric key from the blockchain
        fileKey = pythonModule.callAttr("getFileKey", targetIP, publicKey, privateKey);
    }

    //Function to handle the saving of the URI
    //Returns the path to the destination file
    private byte[] getUploadBytes(String filePath)
    {
        //Now, copy the file from the source directory to the destination
        try
        {
            //Opens an input stream and passes it through several containers to get the final product
            FileInputStream inputStream = new FileInputStream(filePath);
            ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
            byte[] tempBytes = new byte[4096];
            int numBytesRead = inputStream.read(tempBytes);
            while (numBytesRead != -1)
            {
                byteArrayOutputStream.write(tempBytes, 0, numBytesRead);
                numBytesRead = inputStream.read(tempBytes);
            }
            inputStream.close();
            return byteArrayOutputStream.toByteArray();
        }
        //Catches the potential exception
        catch (IOException error)
        {
            Log.e("Cannot read encrypted file", Arrays.toString(error.getStackTrace()));
            throw new RuntimeException();   //Throws an exception to terminate the program as this should never happen
        }
    }

}

//old code
/*
        //Tries to open and read the content of the file
        try
        {
            Toast.makeText(context, filePath, Toast.LENGTH_LONG).show();
            Log.e("File Upload Error1", "Cannot Upload'" + filePath + "' to the blockchain");
            //Creates a new handler for the input file stream using the file path of the resource
            FileInputStream fileInputStream = new FileInputStream(filePath);
            //Creates a new collection of bytes to hold the result
            Log.e("File Upload Error2", "Cannot Upload'" + filePath + "' to the blockchain");
            ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
            //Creates a new byte array 1024 bites long
            Log.e("File Upload Error3", "Cannot Upload'" + filePath + "' to the blockchain");
            byte[] buffer = new byte[1024];
            //Variable holding the bytes read
            Log.e("File Upload Error4", "Cannot Upload'" + filePath + "' to the blockchain");
            int bytesRead = fileInputStream.read(buffer);

            Log.e("File Upload Error4", "Cannot Upload'" + filePath + "' to the blockchain");
            //Loops through all data in the file
            while (bytesRead != -1)
            {

                Log.e("File Upload Error5", "Cannot Upload'" + filePath + "' to the blockchain");
                //Writes the bytes to the byte output stream
                byteArrayOutputStream.write(buffer, 0, bytesRead);
                //Loads the next set of data
                Log.e("File Upload Error6", "Cannot Upload'" + filePath + "' to the blockchain");
                bytesRead = fileInputStream.read(buffer);
            }
            Log.e("File Upload Error7", "Cannot Upload'" + filePath + "' to the blockchain");
            //Converts the content into an array of bytes
            byte[] fileContentToUpload = byteArrayOutputStream.toByteArray();
            //Closes the file input stream
            Log.e("File Upload Error8", "Cannot Upload'" + filePath + "' to the blockchain");
            fileInputStream.close();
            Log.e("File Upload Error9", "Cannot Upload'" + filePath + "' to the blockchain");
            //Closes the byte array output stream
            byteArrayOutputStream.close();
            Log.e("File Upload Error10", "Cannot Upload'" + filePath + "' to the blockchain");
            //Before uploading, refresh the blockchain
            refreshBlockchain();

            Log.e("File Upload Error11", "Cannot Upload'" + filePath + "' to the blockchain");
            //Calls the uploadIpfs() function in Python and sends it the login arguments and returns the result
            pythonModule.callAttr("uploadIpfs", currentUser, fileName, blockchain, fileContentToUpload, fileName);
            //After uploading, refresh the blockchain
            Log.e("File Upload Error12", "Cannot Upload'" + filePath + "' to the blockchain");
            refreshBlockchain();
        }
        //Catches an input exception
        catch (IOException error)
        {
            //Should not happen. But, if it does, log it
            Log.e("File Upload Error", "Cannot Upload'" + filePath + "' to the blockchain");
            return false;       //Returns false to show that the download did not work
        }
        return true;        //Returns true to show that the operation was a success
        */
/*
private void refreshBlockchain():
{

        //if (blockchain != null && blockchain.getClass().getName().equals("java.lang.String"))
        //{
        //    Log.e("Result", blockchain.toJava(String.class));
        //}
        //assert blockchain != null;
        //Log.e("Result", blockchain.toJava(String.class));
        return;
        /*
        //Checks if the result was null
        if (result == null)
        {
            Log.e("null blockchain", "nothing to the blockchain");
            //Do nothing
        }
        //Else, the result is not null
        else
        {
            Log.e("shdflkjshdflkjsdh", "nothing to the blockchain");
            //Creates a new ArrayList to contain the result
            ArrayList<String> listOfActiveUsers = new ArrayList<>();
            //Converts the result from Python list to a list of Python
            List<PyObject> listConversion = result.asList();
            //Loops through all items in the list and returns them as a list
            for (int i = 0; i < listConversion.size(); i++)
            {
                listOfActiveUsers.add(listConversion.get(i).toString());      //Adds the current element to the new list
            }

            Log.e("something to the blockchain", listOfActiveUsers.toString());
            Log.e("something to the blockchain", listConversion.toString());
            blockchain = result;
        }

}
 */