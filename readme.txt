This script allows you to check the status of a Passenger Name Record (PNR) for Indian Railways. It performs the following tasks:

    Accepts a 10-digit PNR number from the user.
    Encrypts the PNR number using AES CBC encryption with PKCS7 padding.
    Sends a POST request to the https://railways.easemytrip.com/Train/PnrchkStatus API endpoint with the encrypted PNR.
    Parses the response from the API and prints the formatted PNR status information, including boarding station, destination station, quota, class name, train number, train name, date of journey, and passenger details.
    Displays the total time taken to complete the program execution.
