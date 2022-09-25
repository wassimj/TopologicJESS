# Use requests (see https://requests.readthedocs.io/en/master/)
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

tab1, tab2, tab3 = st.tabs(["Authentication", "Job Submission", "Job Status"])

with tab1:
    if not st.session_state['cookies']:
        with st.form('Authentication'):
            email = st.text_input('Email')
            password = st.text_input('Password', type='password')
            auth_submitted = st.form_submit_button('Submit')
            if auth_submitted and (not email or not password):
                if not email:
                    st.warning('Email address is missing', icon="⚠️")
                    st.session_state['cookies'] = None
                if not password:
                    st.warning('Password is missing', icon="⚠️")
                    st.session_state['cookies'] = None
            elif auth_submitted and email and password:
                # Set header and body of the POST request
                headers = {'Content-Type': 'application/json'}
                body = {"email": email, "password": password}
                # Send request
                r = requests.post(UserApi + 'auth', headers=headers, json=body)
                if not r.json()['ok']:
                    cookies = None
                    st.session_state['cookies'] = None
                    st.error('ERROR: Wrong Credentials', icon="⚠️")
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
with tab2:
    if st.session_state['cookies']:
        with st.form('energy-analysis'):
            idf_uploaded_file = st.file_uploader('Upload IDF File', type='idf')
            epw_uploaded_file = st.file_uploader('Upload EPW File', type='epw')
            max_sim_time = st.number_input("Maximum Simulation Time (seconds)", min_value=30, max_value=14400, value=300, step=5)
            ea_submitted = st.form_submit_button('Submit')
            if ea_submitted and (not idf_uploaded_file or not epw_uploaded_file):
                if not idf_uploaded_file:
                    st.warning('IDF file is missing', icon="⚠️")
                if not epw_uploaded_file:
                    st.warning('EPW file is missing', icon="⚠️")
            elif ea_submitted and idf_uploaded_file and epw_uploaded_file:
                ea_submitted = False
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
                    ('title', 'Python test case'),
                    ('desc', 'This is test submission made from the API example for Python'),
                    ('split', 'FALSE')
                ]
with tab3:
    if st.session_state['cookies']:
        with st.expander("Job Status", expanded=True):
            with st.spinner("Please wait..."):
                status = 'UNKNOWN'
                if st.button('Cancel Job'):
                    status = 'CANCELLED'
                    st.session_state['status'] = status
                    st.warning('Job Status: CANCELLED', icon="⚠️")
                    # Make a post request. Session token must be available in the saved cookies during log-on
                    r = requests.post('https://api.ensims.com/jess_web/api/job/' + str(st.session_state['job_id']), headers={'Content-Type': 'application/json'}, json={"cmd": "Cancel"}, cookies=st.session_state['cookies'])
                    st.write(r.json())
                elif files:
                # POST with files
                    r = requests.post(JessApi + 'job', files=files, cookies=st.session_state['cookies'])
                # Get job_id. This id number will be needed for querying and retrieving the job data
                    if r.json()['ok']:
                        job_id = r.json()['data']
                        st.session_state['job_id'] = job_id
                        st.info("Job Status: SUBMITTED (ID: "+str(job_id)+")", icon="ℹ️")
                    i = 0
                    while status != 'FINISHED' and status != 'TIMED OUT' and status != 'CANCELLED' and status != 'REJECTED':
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
                    if status == 'FINISHED':
                        st.success('Job Status: FINISHED', icon="✅")
                    elif status == 'TIMED OUT':
                        st.error(' Job Status: TIMED OUT', icon="⚠️")
                    elif status == 'CANCELLED':
                        st.error('Job Status: CANCELLED', icon="⚠️")
                    elif status == 'REJECTED':
                        st.error('Job Status: REJECTED', icon="⚠️")
                    else:
                        st.info("Job Status: "+status)
                    st.session_state['status'] = status

    if st.session_state['status']:
        status = st.session_state['status']
    if st.session_state['job_id']:
        job_id = st.session_state['job_id']
    if st.session_state['cookies']:
        cookies = st.session_state['cookies']
    if st.session_state['status'] == 'FINISHED' and st.session_state['job_id'] and st.session_state['cookies']:
        # GET specific job output with job_id and file name
        if st.session_state['err_data']:
            err_data = st.session_state['err_data']
        else:
            r = requests.get(JessApi + 'job/file/' + str(job_id) + "/eplusout.err", cookies=cookies)
            err_data = r.content
        if st.session_state['sql_data']:
            sql_data = st.session_state['sql_data']
        else:
            r = requests.get(JessApi + 'job/file/' + str(job_id) + "/eplusout.sql", cookies=cookies)
            sql_data = r.content
        if st.session_state['htm_data']:
            htm_data = st.session_state['htm_data']
        else:
            r = requests.get(JessApi + 'job/file/' + str(job_id) + "/eplustbl.htm", cookies=cookies)
            htm_data = r.content
        if st.session_state['csv_data']:
            csv_data = st.session_state['csv_data']
        else:
            r = requests.get(JessApi + 'job/file/' + str(job_id) + "/epluszsz.csv", cookies=cookies)
            csv_data = r.content
        with st.expander("Job Results", expanded=True):
            st.markdown("**ID "+str(job_id)+":**")
            col1, col2, col3, col4 = st.columns(4, gap="medium")
            with col1:
                err_download_btn = st.download_button(
                            label=str(job_id)+".err",
                            data=err_data,
                            file_name=str(job_id)+".err",
                            mime="text/plain"
                        )
            with col2:
                sql_download_btn = st.download_button(
                            label=str(job_id)+".sql",
                            data=sql_data,
                            file_name=str(job_id)+".sql",
                            mime="application/x-sql"
                        )
            with col3:
                htm_download_btn = st.download_button(
                            label=str(job_id)+".htm",
                            data=htm_data,
                            file_name=str(job_id)+".htm",
                            mime="text/html"
                        )
            with col4:
                htm_download_btn = st.download_button(
                            label=str(job_id)+".csv",
                            data=csv_data,
                            file_name=str(job_id)+".csv",
                            mime="text/csv"
                        )

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

