## Packages
from bs4 import BeautifulSoup
import requests
import re
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from pathlib import Path

## Files
from tequila import create_tequila_session

## Login
gaspar = "hoppe"
secret = "ADS#9ijn.1"

## Code

def tequilaLogin(gaspar, secret):
    # Login through tequila
    conn = create_tequila_session(gaspar, secret)
    return conn


def getCourseList(conn):
    response = conn.get("http://moodle.epfl.ch")

    soup = BeautifulSoup(response.content, 'html.parser')

    # Get list of all courses
    courses_html = soup.find_all('div', class_="row coc-course")

    courses = []
    for course in courses_html:
        title_h3 = course.find_all('h3')[0]
        title_a = title_h3.find_all('a')[0]
        title = title_a.get_text()
        
        url = title_h3.find_all('a', href=True)
        
        div_classes = course.find('div', class_="hidecoursediv")["class"]
        if 'coc-hidden' in div_classes:
            isVisible = 0
        else:
            isVisible = 1

        courses.append([title, url[0]['href'], isVisible])
        
    return courses


def getActivityList(conn, course):
    url = course[1]
    
    response = conn.get(url)
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all sections
    sections = soup.find_all('li', class_="section")
    
    # Iterate over sections
    activities = []
    for section in sections:
        
        # Get section name
        section_name = section.find('span', class_='sectionname').contents[0]
              
        # Find all activities
        activity_li = section.find_all('li', class_="activity")
                
        # Iterate over activity elements
        for e in activity_li:
            name = e.find(class_="instancename").contents[0]
            
            ressource_id = e.get('id').split("-")[1]
            
            ressource_type = e["class"][1]
            
            activities.append([name, ressource_id, ressource_type, section_name])
        
    return activities


def buildResourceUrl(id):
    """
    Build ressource url from id
    """
    url = 'https://moodle.epfl.ch/mod/resource/view.php?id=' + id + '&redirect=1'
    return url


def get_filename_from_cd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0]


def downloadResource(conn, path, activity):
    if activity[2] == 'resource':
        id = activity[1]
        url = buildResourceUrl(id)
        
        # Path(path).mkdir(parents=True, exist_ok=True)
        
        response = conn.get(url, allow_redirects=True)
        
        filename = get_filename_from_cd(response.headers.get('content-disposition'))
        
        
        with open(path + '/' + filename.translate({ord('"'): None}), 'wb') as f:
            f.write(response.content)
    

# # Login + Connection
# conn = tequilaLogin(gaspar, secret)

# # Get course list
# courses = getCourseList(conn)

# # Get activity list for first course
# activityList = getActivityList(conn, courses[0])

# Download first pdf ressource from first course
# downloadPath = "C:/Users/Felix/Downloads"
# downloadResource(conn, downloadPath, activityList[1])

### GUI ###

def getUserLogin():
    
    # Get values and login
    def getInputAndLogin():
        gaspar = gasparEntry.get()
        password = passwordEntry.get()
        
        global conn
        
        conn = tequilaLogin(gaspar, password)
        
        # Close window
        loginWindow.destroy()
        
    
    # Define window
    loginWindow = tk.Tk()
    loginWindow.title('EPFL Tequila Login')
    loginWindow.geometry("300x220")

    # Definition of elements
    content = ttk.Frame(master=loginWindow, padding=(3,3,3,3))
    content.pack(fill="both", expand=True)


    titleLabel = tk.Label(master=content, text='Moodle Downloader', font=("Segoe UI", 20, 'bold'), fg='#616161')
    subtitleLabel = tk.Label(master=content, text='Lets login to your EPFL Moodle account', font=("Segoe UI", 12), fg='#616161')
    gasparLabel = tk.Label(master=content, text='Gaspar:', font=("Segoe UI", 10), fg='#616161')
    passwordLabel = tk.Label(master=content, text='Password:', font=("Segoe UI", 10), fg='#616161')
    
    gasparEntry = ttk.Entry(master=content, width=22)
    passwordEntry = ttk.Entry(master=content, width=22, show="*")
    
    
    loginButton = tk.Button(master=content, 
                            text='Login', 
                            font=("Segoe UI", 11), 
                            fg='#616161', 
                            bg='#FFEAEA', 
                            width=15, 
                            height=1, 
                            relief='groove', 
                            command=getInputAndLogin)
    
    # Positioning
    content.grid(column=0, row=0, sticky='NSEW')
    
    titleLabel.grid(column=0, row=0, columnspan=3, padx=(10, 10))
    subtitleLabel.grid(column=0, row=1, columnspan=3, pady=(2, 15))
    
    gasparLabel.grid(column=0, row=2, sticky='w', padx=(15,0), pady=(5,5))
    gasparEntry.grid(column=1, row=2, columnspan=2, padx=(0,15), pady=(5,5))
    passwordLabel.grid(column=0, row=3, sticky='w', padx=(15,0), pady=(5,5))
    passwordEntry.grid(column=1, row=3, columnspan=2, padx=(0,15), pady=(5,5))
    
    loginButton.grid(column=0, row=4, columnspan=3, pady=(17,0))
    
    # Run loop
    loginWindow.mainloop()
    
    return conn


def mainWindow(conn):
        
    #### Define Functions
    def get_download_path():
        """Returns the default downloads path for linux or windows"""
        if os.name == 'nt':
            import winreg
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, downloads_guid)[0]
            return location
        else:
            return os.path.join(os.path.expanduser('~'), 'downloads')
    
    def pickDownloadDir():
        targetDir = filedialog.askdirectory()
        
        # Update text
        downloadFolderOutLabel.config(text=targetDir)
        
    def populateCourseListFrame(conn):
        courseList = getCourseList(conn)
        
        i = 0
        for course in courseList:
            courseLabel = tk.Label(master=courseListFrame, text=course[0], font=("Segoe UI", 10), fg='#616161')
            downloadCourseButton = tk.Button(master=courseListFrame, text='Download', relief='groove',
                                             command = lambda i=i, course=course, conn=conn: downloadCourse(i, course, conn))            
            
            courseLabel.grid(column=0, row=i, sticky='w', padx=(10,0), pady=(3,3))
            downloadCourseButton.grid(column=1, row=i, padx=(10,5), pady=(3,3))
            
            i = i+1
            
    def downloadCourse(i, course, conn):
        # Update label saying that we are currently downloading
        statLabel = tk.Label(master=courseListFrame, text='downloading...', font=("Segoe UI", 10), fg='#616161')
        statLabel.grid(column=2, row=i, padx=(0,5), pady=(3,3))
        statLabel.update()
        
        # Get download path
        path = downloadFolderOutLabel['text']
        
        # Create folder for course
        path = path + "/" + course[0]
        Path(path).mkdir(parents=True, exist_ok=True)
        
        # Get activity list
        activityList = getActivityList(conn, course)
        
        for activity in activityList:
            if activity[2] == 'resource':
                subpath = path + "/" + activity[3]
                Path(subpath).mkdir(parents=True, exist_ok=True)
                downloadResource(conn, subpath, activity)
        
        # Send 'done!' message
        statLabel['text'] = 'done!'
        
    
    #### Build GUI
    mainWindow = tk.Tk()
    mainWindow.title('Moddle Downloader')
    # mainWindow.maxsize(1000, 850)
    
    # Define elements
    content = ttk.Frame(master=mainWindow)
    content.pack(fill="both", expand=True)
    
    leftCol = tk.Frame(master=content, width=700)
    rightCol = tk.Frame(master=content, bg='#FFC692', width=150)
        
    titleLabel = tk.Label(master=leftCol, text='Moodle Downloader', font=("Segoe UI", 20, 'bold'), fg='#616161')
    
    downloadFolderLabel = tk.Label(master=leftCol, text='Download Folder: ', font=("Segoe UI", 10), fg='#616161')
    downloadFolderOutLabel = tk.Label(master=leftCol, text=get_download_path(), font=("Segoe UI", 10), fg='#616161')
    changeDownloadFolderButton = tk.Button(master=leftCol, 
                                           text='Change folder', 
                                           font=("Segoe UI", 9), 
                                           relief='groove', 
                                           command=pickDownloadDir)
    
    courseListTitle = tk.Label(master=leftCol, text='Subscribed courses on Moodle', font=("Segoe UI", 14), fg='#616161')
    courseListFrame = tk.Frame(master=leftCol)
    
    # Place elements
    leftCol.grid(column=0, row=0)
    rightCol.grid(column=1, row=0, sticky='NS')
    
    titleLabel.grid(column=0, row=0, columnspan=3, padx=(10, 10), pady=(0,10), sticky='w')
    
    downloadFolderLabel.grid(column=0, row=1, sticky='w', padx=(5,0))
    downloadFolderOutLabel.grid(column=1, row=1, sticky='w', padx=(0,0))
    changeDownloadFolderButton.grid(column=2, row=1, sticky='w', padx=(0,0))
    
    courseListTitle.grid(column=0, row=2, columnspan=3, sticky='w', padx=(5,0), pady=(10,5))
    courseListFrame.grid(column=0, row=3, columnspan=3, sticky='nsew', pady=(0,20))
    populateCourseListFrame(conn)
    
    # Main loop
    mainWindow.mainloop()



conn = getUserLogin()
# conn = tequilaLogin(gaspar, secret)

mainWindow(conn)

# mainWindow = tk.Tk(className='Moodle downloader')

# # Window style
# mainWindow.geometry("900x600")

# # Two columns (frames)
# leftCol = tk.Frame(master=mainWindow, 
#                    relief=tk.FLAT,
#                    borderwidth=0)
# rightCol = tk.Frame(master=mainWindow, 
#                    relief=tk.FLAT,
#                    borderwidth=0,
#                    background="#FFC692")

# leftCol.grid(row=0, column=0, columnspan=3, sticky="nsew")
# rightCol.grid(row=0, column=5, sticky="nsew")

# label1 = tk.Label(master=leftCol, text="Moodle Downloader", )
# label2 = tk.Label(master=rightCol, text="Right")

# label1.pack()
# label2.pack()

# mainWindow.mainloop()

