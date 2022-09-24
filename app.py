﻿# Use requests (see https://requests.readthedocs.io/en/master/)
import requests
from datetime import date
import time
import os

import streamlit as st

def stringByUploadedFile(uploaded_file):
    return uploaded_file.getvalue().decode('utf-8')

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Topologic JESS Test Application",
    page_icon="📊")

submitted = False

with st.form('energy-analysis'):
    email = st.text_input('Email')
    password = st.text_input('Password', type='password')

    idf_uploaded_file = st.file_uploader('Upload IDF File', type='idf')
    epw_uploaded_file = st.file_uploader('Upload EPW File', type='epw')

    idf_string = None
    epw_string = None

    submitted = st.form_submit_button('Submit')

if submitted and email and password and idf_uploaded_file and epw_uploaded_file:
    if idf_uploaded_file:
        idf_string = stringByUploadedFile(idf_uploaded_file)
        idf_name = idf_uploaded_file.name
    if epw_uploaded_file:
        epw_string = stringByUploadedFile(epw_uploaded_file)
        epw_name = epw_uploaded_file.name

    # API endpoints
    ApiBase = 'https://api.ensims.com/'
    JessApi = ApiBase + "jess_web/api/"
    UserApi = ApiBase + 'users/api/'

    # Set header and body of the POST request
    headers = {'Content-Type': 'application/json'}
    body = {"email": email, "password": password}

    # Send request
    r = requests.post(UserApi + 'auth', headers=headers, json=body)

    # Keep the cookies
    cookies = r.cookies

    # upload a file to a particular folder. Be careful that the file name fields and the model/weather fields must match!
    # upload a file to a particular folder. Be careful that the file name fields and the model/weather fields must match!
    files = [
        ('file', (idf_name, idf_uploaded_file, 'text/plain')),
        ('file', (epw_name, epw_uploaded_file, 'text/plain')),
        ('title', 'Python test case'),
        ('desc', 'This is test submission made from the API example for Python'),
        ('split', 'FALSE')
    ]

    # POST with files
    r = requests.post(JessApi + 'job', files=files, cookies=cookies)
    # Show the returned status
    st.write(r.json())
    # Get job_id. This id number will be needed for querying and retrieving the job data
    job_id = r.json()['data']
    st.write("JOB ID: "+str(job_id))
    time.sleep(10)
    r = requests.get(JessApi + 'job/status/' + str(job_id), cookies=cookies)
    status = r.json()['data']['status']
    st.write(status)
    i = 0
    progress_bar = st.progress(i)
    while status != 'FINISHED' or status != 'TIMED OUT':
        # GET job status with job_id
        time.sleep(30)
        progress_bar.progress(i)
        i = i+5
        if i >= 100:
            status = "TIMED OUT"
        else:
            r = requests.get(JessApi + 'job/status/' + str(job_id), cookies=cookies)
            status = r.json()['data']['status']
    st.write(status)

    if status == 'FINISHED':
        # GET specific job output with job_id and file name
        r = requests.get(JessApi + 'job/file/' + str(job_id) + "/eplusout.err", cookies=cookies)
        st.write(r.content)
        err_btn = st.download_button(
                        label="Download ERR file",
                        data=r.content,
                        file_name=str(job_id)+".err",
                        mime="text/plain"
                    )

        # GET specific job output with job_id and file name
        r = requests.get(JessApi + 'job/file/' + str(job_id) + "/eplusout.sql", cookies=cookies)

        sql_btn = st.download_button(
                        label="Download SQL file",
                        data=r.content,
                        file_name=str(job_id)+".sql",
                        mime="application/x-sql"
                    )

        # GET specific job output with job_id and file name
        r = requests.get(JessApi + 'job/file/' + str(job_id) + "/eplustbl.htm", cookies=cookies)

        htm_btn = st.download_button(
                        label="Download HTML file",
                        data=r.content,
                        file_name=str(job_id)+".htm",
                        mime="text/html"
                    )
