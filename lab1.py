import requests
import pandas as pd
import glob
import os

def download_all_files(directory):
    if(not os.path.exists(directory)):
        print("Create dir...")  # Create the directory if it does not exist
        os.makedirs(directory)
    else:
        print("Dir already exists.")  # Print a message if the directory already exists
    
    if(len(os.listdir(directory))):
        print("Files already exist.")  # Print a message if the files already exist in the directory
    else:
        print("Download files...")  # Print a message indicating that files will be downloaded
        for index in range(1, 29):
            print("Downloading for ID:{}".format(index))  # Print the ID being downloaded
            filename = 'NOA_ID_{}.csv'.format(index)  # Generate the filename based on the index
            url = 'https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH/get_TS_admin.php?country=UKR&provinceID={}&year1=1981&year2=2020&type=Mean'.format(index)  # Generate the URL for downloading the file
            download_file(url,directory+"/"+filename)  # Download the file

def download_file(url,destination):
    response = requests.get(url)  # Send a GET request to the specified URL
    response.raise_for_status()  # Raise an exception if the request was not successful
    with open(destination,'wb') as file:  # Open the file in binary write mode
        file.write(response.content)  # Write the content of the response to the file

def collect_dataframe_from_files(directory):
    headers = ['year', 'week', ' SMN', 'SMT', 'VCI', 'TCI', ' VHI<br>', 'empty']  # Define the headers of real columns
    clear_headers = ['year', 'week', ' SMN', 'SMT', 'VCI', 'TCI', ' VHI<br>']  # Define the headers to use, excluding the last nan column

    dir_files = glob.glob(directory+"/" + "NOA_ID_*.csv")  # Get a list of all files matching the pattern in the directory
    dir_files = sorted(dir_files, key=lambda x: int(x[-6:-4].strip('_')))  # Sort the file list based on the index in the filename

    li = []
    i = 1

    for filename in dir_files:  # Iterate over the file list
        df = pd.read_csv(filename, index_col=None, header=1, names=headers, usecols=clear_headers)  # Read the CSV file into a DataFrame, skipping the first row and using only the specified columns
        df = df.rename(columns={' SMN': 'SMN', ' VHI<br>': 'VHI'})  # Rename the columns
        df = df.drop(df.loc[df['VHI'] == -1].index)  # Drop rows where the VHI column has a value of -1
        df = df.dropna()  # Drop rows with any NaN values

        df['area'] = i  # Add a new column 'area' with the current value of 'i'

        li.append(df)  # Append the DataFrame to the list
        i += 1

    frame = pd.concat(li, axis=0, ignore_index=True)  # Concatenate all DataFrames in the list to create a single DataFrame
    frame["year"].replace({"<tt><pre>1982": "1982"}, inplace=True)  # Replace a specific value in the 'year' column
    return frame

def change_indexes(frame):
    # List with related to LAB indexes. (Original csv set has different ids)
    indexes = ["22", "24", "23", "25", "3", "4", "8", "19", "20", "21", "9", "26", "10", "11",
                            "12", "13", "14", "15", "16", "27", "17", "18", "6", "1", "2", "7", "5"]  # List of new indexes corresponding to the original indexes
    old = 1
    for new in indexes:  # Iterate over the new indexes
        frame["area"].replace({old: new}, inplace=True)  # Replace the old index with the new index in the 'area' column
        old += 1
    frame.to_csv("ALL_CSV_IDobl_UKR_ALL.csv")  # Save the DataFrame to a CSV file
    return frame

def find_hvi_extremums(frame, area_index, year):
    # Get row of vhi for area_index and year
    frame_search = frame[(frame["area"] == area_index) & (frame["year"] == year)]['VHI']  # Select rows where 'area' is equal to 'area_index' and 'year' is equal to 'year' and get the 'VHI' column
    llist = []
    for i in frame_search:
        llist.append(i)
    print(f"Here are VHI for province **{area_index}** in {year}")  # Print a message indicating the province and year
    print(llist)  # Print the VHI values
    print("...")

    max_v = frame[(frame.year.astype(str) == str(year)) & (frame.area == area_index)]['VHI'].max()  # Get the maximum VHI value for the specified year and province
    min_v = frame[(frame.year.astype(str) == str(year)) & (frame.area == area_index)]['VHI'].min()  # Get the minimum VHI value for the specified year and province
    print(f'The MAX value is: {max_v}')  # Print the maximum VHI value
    print(f'The MIN value is: {min_v}')  # Print the minimum VHI value
    print("...")
    return

def find_extreme_mid_weeks(frame,area_index,percent):
    severity_type = {'1':'extreme','2':'mild'}
    severity = input("Choose type of searching:\n1:*extreme*\t2:*mild*: ")  # Prompt the user to choose the type of searching
    if severity == '1':  # If the chosen severity is '1'
        severity_real = 35  # Set the severity_real to 35
    elif severity == '2':  # If the chosen severity is '2'
        severity_real = 60  # Set the severity_real to 60
    else:
        print('Wrong severity')  # Print a message indicating that the severity is wrong
        return

    output = []
    all_possible_years = frame.year.unique()[:]  # Get all possible years from the DataFrame
    frame_search = frame[(frame['area'] == area_index)]  # Select rows where 'area' is equal to 'area_index'
    llist = []
    for i in frame_search["VHI"]:
        llist.append(i)
    print(f"Here are drought VHI for province **{area_index}** in all years")  # Print a message indicating the province
    print(llist)  # Print the VHI values
    print()

    for year in all_possible_years:  # Iterate over all possible years
        current_year = frame_search[(frame_search['year'] == year)]  # Select rows where 'year' is equal to 'year'
        all_weeks = len(current_year.index)  # Count the number of rows

        if severity_real == 35:
            df_drought = current_year[(current_year.VHI <= severity_real)]  # Select rows where VHI is less than or equal to severity_real
        else:
            df_drought = current_year[(current_year.VHI >= severity_real)]  # Select rows where VHI is greater than or equal to severity_real

        extreme_weeks = len(df_drought.index)  # Count the number of extreme weeks
        percentage = extreme_weeks / all_weeks * 100  # Calculate the percentage of extreme weeks
        if percentage >= percent:  # If the percentage is greater than or equal to the specified percent
            output.append(year)  # Add the year to the output list
    print(f"Years with the {severity_type[severity]} droughts with more than {percent}% area:")  # Print a message indicating the severity and percent
    print(output)  # Print the years with extreme droughts

# Main part
directory = 'csv_files'
download_all_files(directory)
frame = collect_dataframe_from_files(directory)
frame = change_indexes(frame)
provinceID = input("Choose ID:")
year = input("Choose year:")
find_hvi_extremums(frame,provinceID,year)
percent = float(input("Choose percent for searching({}):".format(provinceID)))
find_extreme_mid_weeks(frame,provinceID,percent)
