import requests
import urllib3
from bs4 import BeautifulSoup
from flask import request, url_for


def check_dbs_certificate(certificate_number, applicant_surname, applicant_dob, verifier_forename, verifier_surname, organisation_name):

    params = {"dateOfBirth": applicant_dob.strftime("%d/%m/%Y"), "surname": applicant_surname, "organisationName": f"{organisation_name} - API", "employeeForename": verifier_forename, "employeeSurname": verifier_surname, "hasAgreedTermsAndConditions": "true"}
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1' # Reqired due to DBS system supporting older ciphers - https://stackoverflow.com/questions/38015537/python-requests-exceptions-sslerror-dh-key-too-small
    r = requests.get(f"https://secure.crbonline.gov.uk/crsc/api/status/{certificate_number}", params=params)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, features="html.parser")
        status = soup.find("status").string
        if status == "NO_MATCH_FOUND" or status == "NEW_INFO":
            return False
        elif status == "NON_BLANK_NO_NEW_INFO" or "BLANK_NO_NEW_INFO":
            return True
    return False


def redirect_url(default='admin_routes.admin_home'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)