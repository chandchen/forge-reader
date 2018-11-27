# -*- coding: utf-8 -*-
import requests

from django.conf import settings

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from forgereader.core.models import (
    ForgeUser, Milestone, Label, Issue, Project)


headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
                  AppleWebKit/537.36 (KHTML, like Gecko) \
                  Chrome/59.0.3071.115 Safari/537.36",
    'Referer': settings.FORGE_URL
}

sessions = requests.Session()


class Authentication:

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.login_url = settings.FORGE_URL + '/users/sign_in'

    def login(self):
        html = sessions.get(self.login_url, headers=headers).text
        soup = BeautifulSoup(html, features="html.parser")
        token = soup.select('input[name="authenticity_token"]')[0].get('value')
        data = {
            'user[login]': self.email,
            'user[password]': self.password,
            'authenticity_token': token
        }
        r = sessions.post(self.login_url, data=data)
        if r.status_code == 200:
            print('Login Success!')
        else:
            print('Login Failed!')


def fetch_issue_detail(project, issue):
    repo_url = settings.FORGE_URL + '/{}/issues/{}'.format(
        project.repo_name, issue)
    url = repo_url.replace(' ', '')
    html = sessions.get(url, headers=headers).text
    soup = BeautifulSoup(html, features="html.parser")

    try:
        milestone = soup.find(
            'div', class_="milestone").find('div', class_="value").find(
            'a', class_="bold").get_text().replace('\n', '')
    except Exception as e:
        milestone = ''
    timeline = update_timeline_data(url)
    return {
        'milestone': milestone,
        'timeline': timeline,
    }


def fetch_issue_list(project, url):
    html = sessions.get(url, headers=headers).text
    soup = BeautifulSoup(html, features="html.parser")

    contents = soup.find(
        'ul', class_="issues-list").findAll('li', class_="issue")

    for content in contents:
        try:
            title = content.find(
                'span', class_="issue-title-text").get_text().replace('\n', '')
        except Exception as e:
            title = ''
        try:
            number = content.find(
                'span', class_="issuable-reference").get_text().replace(
                '\n', '').replace('#', '')
        except Exception as e:
            number = ''
        try:
            author = content.find(
                'span', class_="author").get_text().replace('\n', '')
        except Exception as e:
            author = ''

        if author:
            author = ForgeUser.objects.filter(full_name=author).first()
        else:
            author = None

        try:
            assignee = content.find(
                'div', class_="issuable-meta").find(
                'a', class_="author-link")['title'].replace(
                '\n', '').replace('Assigned to ', '')
        except Exception as e:
            assignee = ''

        if assignee:
            assignee = ForgeUser.objects.filter(full_name=assignee).first()
        else:
            assignee = None

        try:
            status = content.find(
                'li', class_="issuable-status").get_text().replace('\n', '')
        except Exception as e:
            status = ''

        if status == 'CLOSED':
            status = Issue.CLOSED
        else:
            status = Issue.OPEN

        labels = []
        try:
            xlabels = content.findAll('a', class_="label-link")
            if xlabels:
                for label in xlabels:
                    labels.append(label.find('span').get_text())
        except Exception as e:
            labels = []

        extra_info = fetch_issue_detail(project, number)

        milestone = extra_info['milestone']

        if milestone:
            milestone = Milestone.objects.filter(name=milestone).first()
        else:
            milestone = None

        infos = {
            'title': title,
            'author': author,
            'assignee': assignee,
            'number': int(number),
            'status': status,
            'milestone': milestone,
            'project': project
        }

        obj, created = Issue.objects.update_or_create(
            number=int(number), defaults=infos)

        if labels:
            label = Label.objects.filter(name__in=labels)
            if label.exists():
                obj.labels.add(*label)


def update_issue_data(project=None):
    # cs = Authentication(settings.FORGE_USERNAME, settings.FORGE_PASSWORD)
    # cs.login()

    # project = Project.objects.filter(
    #     name='channelfix', namespace='channelfix').first()
    index_url = settings.FORGE_URL + '/{}/issues?scope=all&utf8=✓&\
        state=all'.format(project.repo_name)
    html0 = sessions.get(index_url, headers=headers).text
    soup0 = BeautifulSoup(html0, features="html.parser")
    try:
        bottom = soup0.findAll(
            'li', class_="js-pagination-page")[-1].get_text().replace('\n', '')
    except Exception as e:
        bottom = 1
    for i in range(1, int(bottom) + 1):
        url = settings.FORGE_URL + '/{}/issues?page={}&scope=all&\
            state=all'.format(project.repo_name, i)
        fetch_issue_list(project, url)


def update_milestone_data(project):
    # cs = Authentication(settings.FORGE_USERNAME, settings.FORGE_PASSWORD)
    # cs.login()

    repo_url = settings.FORGE_URL + '/{}/milestones\
        ?sort=due_date_desc&state=all'.format(project.repo_name)
    url = repo_url.replace(' ', '')
    html = sessions.get(url, headers=headers).text
    soup = BeautifulSoup(html, features="html.parser")

    contents = soup.find(
        'ul', class_="content-list").findAll('li', class_="milestone")

    for content in contents:
        try:
            name = content.find(
                'div', class_="append-bottom-5").get_text().replace('\n', '')
        except Exception as e:
            name = ''
        try:
            milestone_range = content.find(
                'div', class_="milestone-range").get_text().replace('\n', '')
        except Exception as e:
            milestone_range = ''
        try:
            status = content.find(
                'div', class_="status-box").get_text().replace('\n', '')
        except Exception as e:
            status = ''

        if name:
            Milestone.objects.update_or_create(
                name=name, defaults={
                    'name': name,
                    'milestone_range': milestone_range,
                    'status': status,
                    'project': project})


def update_label_data(project):
    # cs = Authentication(settings.FORGE_USERNAME, settings.FORGE_PASSWORD)
    # cs.login()

    index_url = settings.FORGE_URL + '/{}/labels'.format(project.repo_name)
    html0 = sessions.get(index_url, headers=headers).text
    soup0 = BeautifulSoup(html0, features="html.parser")
    try:
        bottom = soup0.findAll(
            'li', class_="js-pagination-page")[-1].get_text().replace('\n', '')
    except Exception as e:
        bottom = 1
    for i in range(1, int(bottom) + 1):
        repo_url = settings.FORGE_URL + '/{}/labels?page={}'.format(
            project.repo_name, i)
        url = repo_url.replace(' ', '')
        html = sessions.get(url, headers=headers).text
        soup = BeautifulSoup(html, features="html.parser")

        contents = soup.find(
            'div', class_="other-labels").findAll(
            'li', class_="label-list-item")

        for content in contents:
            try:
                name = content.find(
                    'div', class_="label-name").get_text().replace('\n', '')
            except Exception as e:
                name = ''

            try:
                description = content.find(
                    'div',
                    class_="description-text").get_text().replace('\n', '')
            except Exception as e:
                description = ''
            if name:
                Label.objects.update_or_create(
                    name=name, defaults={
                        'name': name,
                        'description': description,
                        'project': project
                    })


def update_forgeuser_data():
    # cs = Authentication(settings.FORGE_USERNAME, settings.FORGE_PASSWORD)
    # cs.login()

    index_url = settings.FORGE_URL + '/{}/project_members?'.format(
        settings.DEFAULT_REPO)
    html0 = sessions.get(index_url, headers=headers).text
    soup0 = BeautifulSoup(html0, features="html.parser")
    try:
        bottom = soup0.findAll(
            'li', class_="js-pagination-page")[-1].get_text().replace('\n', '')
    except Exception as e:
        bottom = 1
    for i in range(1, int(bottom) + 1):
        repo_url = settings.FORGE_URL + '/{}/project_members?page\
            ={}'.format(settings.DEFAULT_REPO, i)
        url = repo_url.replace(' ', '')
        html = sessions.get(url, headers=headers).text
        soup = BeautifulSoup(html, features="html.parser")

        contents = soup.find(
            'ul', class_="members-list").findAll(
            'li', class_="group_member")

        for content in contents:
            try:
                username = content.find(
                    'span', class_="cgray").get_text().replace(
                    '\n', '').replace('@', '')
            except Exception as e:
                username = ''
            try:
                full_name = content.find(
                    'a', class_="member").get_text().replace('\n', '')
            except Exception as e:
                full_name = ''
            if username:
                ForgeUser.objects.update_or_create(
                    username=username, defaults={
                        'username': username,
                        'full_name': full_name
                    })


def update_project_data():
    # cs = Authentication(settings.FORGE_USERNAME, settings.FORGE_PASSWORD)
    # cs.login()

    html0 = sessions.get(settings.FORGE_URL, headers=headers).text
    soup0 = BeautifulSoup(html0, features="html.parser")
    try:
        bottom = soup0.findAll(
            'li', class_="js-pagination-page")[-1].get_text().replace('\n', '')
    except Exception as e:
        bottom = 1
    for i in range(1, int(bottom) + 1):
        repo_url = settings.FORGE_URL + '/?non_archived=true&page={}&sort=\
            latest_activity_desc'.format(i)
        url = repo_url.replace(' ', '')
        html = sessions.get(url, headers=headers).text
        soup = BeautifulSoup(html, features="html.parser")
        contents = soup.find(
            'ul', class_="projects-list").findAll(
            'li', class_="project-row")

        for content in contents:
            try:
                namespace = content.find(
                    'span', class_="namespace-name").get_text().replace(
                    '\n', '').replace('/', '')
            except Exception as e:
                namespace = ''

            try:
                name = content.find(
                    'span', class_="project-name").get_text().replace(
                    '\n', '')
            except Exception as e:
                name = ''
            if namespace and name:
                Project.objects.update_or_create(
                    name=name,
                    namespace=namespace,
                    defaults={'name': name, 'namespace': namespace})


def update_forge_data():
    cs = Authentication(settings.FORGE_USERNAME, settings.FORGE_PASSWORD)
    cs.login()

    # update_project_data()
    # update_forgeuser_data()

    projects = Project.objects.filter(
        namespace=settings.REPO_NAMESPACE,
        name__in=settings.REPO_NAME)
    if projects.exists():
        for project in projects:
            update_label_data(project=project)
            update_milestone_data(project=project)
            update_issue_data(project=project)
    print('Greeting, All data up to date!')


def webdriver_login(driver, account, passwd):
    driver.find_element_by_id('user_login').send_keys(account)
    driver.find_element_by_id('user_password').send_keys(passwd)
    driver.find_element_by_class_name('btn-save').click()

    title = driver.find_element_by_class_name('shortcuts-activity').text
    try:
        assert title == 'Your projects'
        print('Login Success!')
    except AssertionError as e:
        print('Login Failed!')
    return driver


def fetch_timeline_info(driver, url):
    driver.get(url)
    driver.implicitly_wait(10)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((
            By.XPATH, '//*[@id="notes-list"]')))

    ul = driver.find_element_by_id('notes-list')
    contents = ul.find_elements_by_xpath('li')
    for content in contents:
        try:
            username = content.find_element_by_class_name(
                'note-headline-light').text
            print(username)
        except Exception as e:
            pass

        try:
            action = content.find_element_by_class_name(
                'system-note-message').find_element_by_xpath('span').text
            print(action)
        except Exception as e:
            pass

        try:
            time = content.find_element_by_tag_name(
                'time').get_attribute('data-original-title')
            print(time)
        except Exception as e:
            pass


def update_timeline_data(url):
    driver = webdriver.Chrome()
    driver.get(settings.FORGE_URL)
    driver.maximize_window()
    driver = webdriver_login(
        driver, settings.FORGE_USERNAME, settings.FORGE_PASSWORD)
    fetch_timeline_info(driver, url)
    driver.quit()
