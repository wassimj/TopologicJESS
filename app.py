# Use requests (see https://requests.readthedocs.io/en/master/)
import requests
from datetime import date
import time
import os

import streamlit as st
import math

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Topologic JESS Test Application",
    page_icon="🏢")

submitted = False

if 'attempts' not in st.session_state:
    attempts = -1
    st.session_state['attempts'] = -1
if 'status' not in st.session_state:
    status = None
    st.session_state['status'] = None
if 'job_id' not in st.session_state:
    job_id = None
    st.session_state['job_id'] = None
if 'cookies' not in st.session_state:
    cookies = None
    st.session_state['cookies'] = None
if 'err_data' not in st.session_state:
    err_data = None
    st.session_state['err_data'] = None
if 'sql_data' not in st.session_state:
    sql_data = None
    st.session_state['sql_data'] = None
if 'htm_data' not in st.session_state:
    htm_data = None
    st.session_state['htm_data'] = None
if 'csv_data' not in st.session_state:
    csv_data = None
    st.session_state['csv_data'] = None
# API endpoints
ApiBase = 'https://api.ensims.com/'
JessApi = ApiBase + "jess_web/api/"
UserApi = ApiBase + 'users/api/'
files = None

tab1, tab2, tab3, tab4 = st.tabs(["Authentication", "Submission", "Status", "History"])

with tab1:
    if not st.session_state['cookies']:
        if st.session_state['attempts'] == -1:
            st.session_state['attempts'] = 1
        else:
            st.session_state['attempts'] = st.session_state['attempts'] + math.floor(st.session_state['attempts']*0.1)
        time.sleep(st.session_state['attempts'])
        with st.expander("Terms of Service", expanded = False):
            st.markdown("**Disclaimer**. This software and any service provided by this software is not guaranteed to be free from defects. This software and any service provided by this software is provided **as is** and you use them at your own risk. No warranties as to performance, merchantability, fitness for a particular purpose, or any other warranties whether expressed or implied are made. No oral or written communication from or information provided by the authors of this software and any services provided by this software shall create a warranty. Under no circumstances shall the authors of this software or any services provided by this software be liable for direct, indirect, special, incidental, or consequential damages resulting from the use, misuse, or inability to use this software or any services provided by this software, even if the authors of this software or any services provided by this software have been advised of the possibility of such damages.")
            st.markdown("**No Reverse Engineering**. You may not, and you agree not to or enable others to, copy, decompile, reverse engineer, disassemble, attempt to derive the source code of, decrypt, modify, or create derivative works of this software or any services provided by this software, or any part thereof (except as and only to the extent any foregoing restriction is prohibited by applicable law or to the extent as may be permitted by the licensing terms governing use of open-sourced components included with this software and any services provided by this software).")
        with st.form('Authentication'):
            email = st.text_input('Email')
            password = st.text_input('Password', type='password')
            agree = st.checkbox('I agree to the terms of service listed above')
            auth_submitted = st.form_submit_button('Submit')
            if auth_submitted and (not email or not password or not agree):
                if not email:
                    st.warning('Email address is missing', icon="⚠️")
                    st.session_state['cookies'] = None
                if not password:
                    st.warning('Password is missing', icon="⚠️")
                    st.session_state['cookies'] = None
                if not agree:
                    st.warning('You have not agreed to the terms of service', icon="⚠️")
                    st.session_state['cookies'] = None
            elif auth_submitted and email and password and agree:
                # Set header and body of the POST request
                headers = {'Content-Type': 'application/json'}
                body = {"email": email, "password": password}
                # Send request
                r = requests.post(UserApi + 'auth', headers=headers, json=body)
                if not r.json()['ok']:
                    cookies = None
                    st.session_state['cookies'] = None
                    st.error('Wrong credentials', icon="❌")
                else:
                    # Keep the cookies
                    cookies = r.cookies
                    st.session_state['cookies'] = cookies

    if st.session_state['cookies']:
        col1, col2 = st.columns([5,1], gap="large")
        with col1:
            st.success('LOGGED IN', icon="✅")
        with col2:
            if st.button('Log Out'):
                cookies = None
                st.session_state['cookies'] = None
                st.session_state['attempts'] = -1
                time.sleep(5)
with tab2:
    if st.session_state['cookies']:
        with st.form('energy-analysis'):
            idf_uploaded_file = st.file_uploader('Upload IDF File', type='idf')
            epw_uploaded_file = st.file_uploader('Upload EPW File', type='epw')
            title = st.text_input("Project Name", "Untitled")
            description = st.text_input("Description", "Describe your project here")
            max_sim_time = st.number_input("Maximum Simulation Time (seconds)", min_value=30, max_value=14400, value=300, step=5)
            ea_submitted = st.form_submit_button('Submit')
            if ea_submitted and (not idf_uploaded_file or not epw_uploaded_file):
                if not idf_uploaded_file:
                    st.warning('IDF file is missing', icon="⚠️")
                if not epw_uploaded_file:
                    st.warning('EPW file is missing', icon="⚠️")
            elif ea_submitted and idf_uploaded_file and epw_uploaded_file:
                err_data = None
                st.session_state['err_data'] = None
                sql_data = None
                st.session_state['sql_data'] = None
                htm_data = None
                st.session_state['htm_data'] = None
                idf_name = idf_uploaded_file.name
                epw_name = epw_uploaded_file.name

                # upload a file to a particular folder. Be careful that the file name fields and the model/weather fields must match!
                # upload a file to a particular folder. Be careful that the file name fields and the model/weather fields must match!
                files = [
                    ('file', (idf_name, idf_uploaded_file, 'text/plain')),
                    ('file', (epw_name, epw_uploaded_file, 'text/plain')),
                    ('title', title),
                    ('desc', description),
                    ('split', 'FALSE')
                ]
        if ea_submitted and files:
            with st.spinner("Please wait..."):
                # POST with files
                    r = requests.post(JessApi + 'job', files=files, cookies=st.session_state['cookies'])
                # Get job_id. This id number will be needed for querying and retrieving the job data
                    if r.json()['ok']:
                        job_id = r.json()['data']
                        st.session_state['job_id'] = job_id
                        st.info("Job Status: SUBMITTED (ID: "+str(job_id)+")", icon="ℹ️")
    else:
        st.warning('Please log in.', icon="⚠️")
with tab3:
    if st.session_state['cookies']:
        if ea_submitted:
            st.markdown("**Job ID "+str(st.session_state['job_id'])+"**")
            status = 'UNKNOWN'
            st.session_state['status'] = status
            if st.button('Cancel Job'):
                status = 'CANCELLED'
                st.session_state['status'] = status
                st.warning('Job Status: CANCELLED', icon="⚠️")
                # Make a post request. Session token must be available in the saved cookies during log-on
                r = requests.post('https://api.ensims.com/jess_web/api/job/' + str(st.session_state['job_id']), headers={'Content-Type': 'application/json'}, json={"cmd": "Cancel"}, cookies=st.session_state['cookies'])
                st.write(r.json())
            ea_submitted = False
            with st.expander("Job Status", expanded=True):
                with st.spinner("Please wait..."):
                    i = 0
                    while st.session_state['status'] != 'FINISHED' and st.session_state['status'] != 'TIMED OUT' and st.session_state['status'] != 'CANCELLED' and st.session_state['status'] != 'REJECTED':
                        # GET job status with job_id
                        time.sleep(30)
                        i = i+30
                        if i >= max_sim_time:
                            status = "TIMED OUT"
                            st.session_state['status'] = status
                            r = requests.post('https://api.ensims.com/jess_web/api/job/' + str(st.session_state['job_id']), headers={'Content-Type': 'application/json'}, json={"cmd": "Cancel"}, cookies=st.session_state['cookies'])
                        else:
                            r = requests.get(JessApi + 'job/status/' + str(st.session_state['job_id']), cookies=st.session_state['cookies'])
                            try:
                                status = r.json()['data']['status']
                                st.session_state['status'] = status
                                if status != "FINISHED" and status != "CANCELLED" and status != "TIMED OUT" and status != "REJECTED":
                                    st.info("Job Status: "+status, icon="ℹ️")
                            except:
                                st.warning('Job Status: UNKNOWN', icon="⚠️")
                                status = 'UNKNOWN'
                                st.session_state['status'] = status
                    if st.session_state['status'] == 'TIMED OUT':
                        st.error(' Job Status: TIMED OUT', icon="⚠️")
                    elif st.session_state['status'] == 'CANCELLED':
                        st.error('Job Status: CANCELLED', icon="⚠️")
                    elif st.session_state['status'] == 'REJECTED':
                        st.error('Job Status: REJECTED', icon="⚠️")
                    else:
                        st.info("Job Status: "+status)
        else:
            st.warning('Please submit a job.', icon="⚠️")
    else:
        st.warning('Please log in.', icon="⚠️")
    if st.session_state['status'] == 'FINISHED' and st.session_state['job_id'] and st.session_state['cookies']:
        st.success('Job Status: FINISHED', icon="✅")
        # GET specific job output with job_id and file name
        if st.session_state['err_data']:
            err_data = st.session_state['err_data']
        else:
            r = requests.get(JessApi + 'job/file/' + str(st.session_state['job_id']) + "/eplusout.err", cookies=st.session_state['cookies'])
            err_data = r.content
        if st.session_state['sql_data']:
            sql_data = st.session_state['sql_data']
        else:
            r = requests.get(JessApi + 'job/file/' + str(st.session_state['job_id']) + "/eplusout.sql", cookies=st.session_state['cookies'])
            sql_data = r.content
        if st.session_state['htm_data']:
            htm_data = st.session_state['htm_data']
        else:
            r = requests.get(JessApi + 'job/file/' + str(st.session_state['job_id']) + "/eplustbl.htm", cookies=st.session_state['cookies'])
            htm_data = r.content
        if st.session_state['csv_data']:
            csv_data = st.session_state['csv_data']
        else:
            r = requests.get(JessApi + 'job/file/' + str(st.session_state['job_id']) + "/epluszsz.csv", cookies=st.session_state['cookies'])
            csv_data = r.content
        with st.expander("Job Results", expanded=True):
            col1, col2, col3, col4 = st.columns(4, gap="medium")
            with col1:
                err_download_btn = st.download_button(
                            label=str(st.session_state['job_id'])+".err",
                            data=err_data,
                            file_name=str(st.session_state['job_id'])+".err",
                            mime="text/plain"
                        )
            with col2:
                sql_download_btn = st.download_button(
                            label=str(st.session_state['job_id'])+".sql",
                            data=sql_data,
                            file_name=str(st.session_state['job_id'])+".sql",
                            mime="application/x-sql"
                        )
            with col3:
                htm_download_btn = st.download_button(
                            label=str(st.session_state['job_id'])+".htm",
                            data=htm_data,
                            file_name=str(st.session_state['job_id'])+".htm",
                            mime="text/html"
                        )
            with col4:
                htm_download_btn = st.download_button(
                            label=str(st.session_state['job_id'])+".csv",
                            data=csv_data,
                            file_name=str(st.session_state['job_id'])+".csv",
                            mime="text/csv"
                        )

with tab4:
    if st.session_state['cookies']:
        with st.expander("Finished Jobs List", expanded=False):
            # GET the list of jobs fit the given criteria
            filter = {"status": "FINISHED"}
            r = requests.get(JessApi + 'jobs', headers={'Content-Type': 'application/json'}, json=filter, cookies=st.session_state['cookies'])
            st.write(r.json())
        with st.expander("Rejected Jobs List", expanded=False):
            # GET the list of jobs fit the given criteria
            filter = {"status": "REJECTED"}
            r = requests.get(JessApi + 'jobs', headers={'Content-Type': 'application/json'}, json=filter, cookies=st.session_state['cookies'])
            st.write(r.json())
    else:
        st.warning('Please log in.', icon="⚠️")

