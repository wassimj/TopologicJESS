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

if 'status' not in st.session_state:
    status = None
    st.session_state['status'] = None
if 'job_id' not in st.session_state:
    job_id = None
    st.session_state['job_id'] = None
if 'cookies' not in st.session_state:
    cookies = None
    st.session_state['cookies'] = None
# API endpoints
ApiBase = 'https://api.ensims.com/'
JessApi = ApiBase + "jess_web/api/"
UserApi = ApiBase + 'users/api/'

with st.form('energy-analysis'):
    email = st.text_input('Email')
    password = st.text_input('Password', type='password')
    idf_uploaded_file = st.file_uploader('Upload IDF File', type='idf')
    epw_uploaded_file = st.file_uploader('Upload EPW File', type='epw')
    submitted = st.form_submit_button('Submit')

if submitted and email and password and idf_uploaded_file and epw_uploaded_file:
    submitted = False
    # Set header and body of the POST request
    headers = {'Content-Type': 'application/json'}
    body = {"email": email, "password": password}
    idf_name = idf_uploaded_file.name
    epw_name = epw_uploaded_file.name

    # Send request
    r = requests.post(UserApi + 'auth', headers=headers, json=body)

    # Keep the cookies
    cookies = r.cookies
    st.session_state['cookies'] = cookies

    # upload a file to a particular folder. Be careful that the file name fields and the model/weather fields must match!
    # upload a file to a particular folder. Be careful that the file name fields and the model/weather fields must match!
    files = [
        ('file', (idf_name, idf_uploaded_file, 'text/plain')),
        ('file', (epw_name, epw_uploaded_file, 'text/plain')),
        ('title', 'Python test case'),
        ('desc', 'This is test submission made from the API example for Python'),
        ('split', 'FALSE')
    ]

    with st.spinner("Please wait..."):
        status = 'UNKNOWN'
        # POST with files
        r = requests.post(JessApi + 'job', files=files, cookies=cookies)
        # Get job_id. This id number will be needed for querying and retrieving the job data
        if r.json()['ok']:
            job_id = r.json()['data']
            st.session_state['job_id'] = job_id
            st.info("Job Status: SUBMITTED (ID: "+str(job_id)+")", icon="✅")
            #time.sleep(10)
            #r = requests.get(JessApi + 'job/status/' + str(job_id), cookies=cookies)
            #status = r.json()['data']['status']
            #st.write("Job Status: "+status)
            i = 0
            while status != 'FINISHED' and status != 'TIMED OUT':
                # GET job status with job_id
                time.sleep(30)
                i = i+5
                if i >= 100:
                    status = "TIMED OUT"
                else:
                    r = requests.get(JessApi + 'job/status/' + str(job_id), cookies=cookies)
                    try:
                        status = r.json()['data']['status']
                    except:
                        st.warning('Job Status: UNKNOWN', icon="⚠️")
                        status = 'UNKNOWN'
            if status == 'FINISHED':
                st.success('Job Status: FINISHED', icon="✅")
            elif status == 'TIMED OUT':
                st.error('Job Status: TIMED OUT', icon="⚠️")
            else:
                st.info("Job Status: "+status)
            st.session_state['status'] = status

if st.session_state['status']:
    status = st.session_state['status']
if st.session_state['job_id']:
    job_id = st.session_state['job_id']
if st.session_state['cookies']:
    cookies = st.session_state['cookies']
if st.session_state['status'] and st.session_state['job_id'] and st.session_state['cookies']:
    # GET specific job output with job_id and file name
    r = requests.get(JessApi + 'job/file/' + str(job_id) + "/eplusout.err", cookies=cookies)
    err_data = r.content
    r = requests.get(JessApi + 'job/file/' + str(job_id) + "/eplusout.sql", cookies=cookies)
    sql_data = r.content
    r = requests.get(JessApi + 'job/file/' + str(job_id) + "/eplustbl.htm", cookies=cookies)
    htm_data = r.content
    option = st.selectbox(
    'What file would you like to download?',
    ('ERR', 'SQL', 'HTM'))

    if option == "ERR":
        data = err_data
        mime = "text/plain"
    elif option == "SQL":
        data = sql_data
        mime="application/x-sql"
    else:
        data = htm_data
        mime="text/html"

    download_btn = st.download_button(
                    label="Download "+option+" file",
                    data=data,
                    file_name=str(job_id)+"."+option.lower(),
                    mime=mime
                )
 

