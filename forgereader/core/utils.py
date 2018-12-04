# -*- coding: utf-8 -*-
import requests
import csv

from django.utils import timezone

from django.conf import settings

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from forgereader.core.models import (
    User, Milestone, Label, Issue, Project, Action)


headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
                  AppleWebKit/537.36 (KHTML, like Gecko) \
                  Chrome/59.0.3071.115 Safari/537.36",
    'Referer': settings.SITE_URL
}

sessions = requests.Session()


class Authentication:

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.login_url = settings.SITE_URL + '/users/sign_in'

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
    repo_url = settings.SITE_URL + '/{}/issues/{}'.format(
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
    return {
        'milestone': milestone,
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
            author = User.objects.filter(full_name=author).first()
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
            assignee = User.objects.filter(full_name=assignee).first()
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
    # cs = Authentication(settings.USERNAME, settings.PASSWORD)
    # cs.login()

    # project = Project.objects.filter(
    #     name='channelfix', namespace='channelfix').first()
    index_url = settings.SITE_URL + '/{}/issues?scope=all&utf8=✓&\
        state=all'.format(project.repo_name)
    html0 = sessions.get(index_url, headers=headers).text
    soup0 = BeautifulSoup(html0, features="html.parser")
    # WARNING: Wrong pagination here
    try:
        bottom = soup0.findAll(
            'li', class_="js-pagination-page")[-1].get_text().replace('\n', '')
    except Exception as e:
        bottom = 1
    for i in range(1, int(bottom) + 1):
        url = settings.SITE_URL + '/{}/issues?page={}&scope=all&\
            state=all'.format(project.repo_name, i)
        fetch_issue_list(project, url)


def update_milestone_data(project):
    # cs = Authentication(settings.USERNAME, settings.PASSWORD)
    # cs.login()

    repo_url = settings.SITE_URL + '/{}/milestones\
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
                name=name,
                project=project,
                defaults={
                    'name': name,
                    'milestone_range': milestone_range,
                    'status': status,
                    'project': project})


def update_label_data(project):
    # cs = Authentication(settings.USERNAME, settings.PASSWORD)
    # cs.login()

    index_url = settings.SITE_URL + '/{}/labels'.format(project.repo_name)
    html0 = sessions.get(index_url, headers=headers).text
    soup0 = BeautifulSoup(html0, features="html.parser")
    try:
        bottom = soup0.findAll(
            'li', class_="js-pagination-page")[-1].get_text().replace('\n', '')
    except Exception as e:
        bottom = 1
    for i in range(1, int(bottom) + 1):
        repo_url = settings.SITE_URL + '/{}/labels?page={}'.format(
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
                    name=name,
                    project=project,
                    defaults={
                        'name': name,
                        'description': description,
                        'project': project
                    })


def update_user_data():
    # cs = Authentication(settings.USERNAME, settings.PASSWORD)
    # cs.login()

    index_url = settings.SITE_URL + '/{}/project_members?'.format(
        settings.DEFAULT_REPO)
    html0 = sessions.get(index_url, headers=headers).text
    soup0 = BeautifulSoup(html0, features="html.parser")
    try:
        bottom = soup0.findAll(
            'li', class_="js-pagination-page")[-1].get_text().replace('\n', '')
    except Exception as e:
        bottom = 1
    for i in range(1, int(bottom) + 1):
        repo_url = settings.SITE_URL + '/{}/project_members?page\
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
                User.objects.update_or_create(
                    username=username, defaults={
                        'username': username,
                        'full_name': full_name
                    })


def update_project_data():
    # cs = Authentication(settings.USERNAME, settings.PASSWORD)
    # cs.login()

    html0 = sessions.get(settings.SITE_URL, headers=headers).text
    soup0 = BeautifulSoup(html0, features="html.parser")
    try:
        bottom = soup0.findAll(
            'li', class_="js-pagination-page")[-1].get_text().replace('\n', '')
    except Exception as e:
        bottom = 1
    for i in range(1, int(bottom) + 1):
        repo_url = settings.SITE_URL + '/?non_archived=true&page={}&sort=\
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


def update_remote_data():
    cs = Authentication(settings.USERNAME, settings.PASSWORD)
    cs.login()

    update_project_data()
    update_user_data()

    projects = Project.objects.filter(
        namespace=settings.REPO_NAMESPACE,
        name__in=settings.REPO_NAME)
    if projects.exists():
        for project in projects:
            update_label_data(project=project)
            update_milestone_data(project=project)
    return True


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


def fetch_timeline_info(driver, issue=None):
    # url = settings.SITE_URL + '/{}/issues/{}'.format(
    #     issue.project.repo_name, issue.number)
    # driver.get(url)
    # driver.implicitly_wait(100)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((
            By.XPATH, '//*[@id="notes-list"]')))

    try:
        ul = driver.find_element_by_id('notes-list')
        contents = ul.find_elements_by_xpath('li')
        for content in contents:
            try:
                username = content.find_element_by_class_name(
                    'note-headline-light').text.replace('@', '')
            except Exception as e:
                username = ''

            try:
                action = content.find_element_by_class_name(
                    'system-note-message').find_element_by_xpath('span').text
            except Exception as e:
                action = ''

            try:
                original_time = content.find_element_by_tag_name(
                    'time').get_attribute('data-original-title')
                format_time = timezone.datetime.strptime(
                    original_time, '%b %d, %Y %I:%M%p GMT%z')
            except Exception as e:
                format_time = None
            contents = {
                'username': username,
                'action': action,
                'format_time': format_time,
            }

            if username:
                owner = User.objects.filter(username=username).first()
                if owner:
                    a, msg = Action.objects.update_or_create(
                        issue=issue,
                        owner=owner,
                        created=format_time,
                        action=action,
                        defaults={
                            'issue': issue,
                            'owner': owner,
                            'created': format_time,
                            'action': action
                        }
                    )
    except Exception as e:
        print('WARNING: Failed Timeline in #{}'.format(1))


def fetch_issue_detail_info(driver, issue_url, num, project):
    driver.get(issue_url)
    # driver.implicitly_wait(10)
    # time.sleep(5)
    print('Loading #{}'.format(num))

    try:
        headers = driver.find_element_by_class_name('detail-page-header-body')
        status = headers.find_element_by_class_name(
            'status-box-issue-closed').text
        # status2 = headers.find_element_by_class_name(
        #     'status-box-open').text
        status = Issue.CLOSED if status else Issue.OPEN

        created = headers.find_element_by_tag_name(
            'time').get_attribute('data-original-title') + '-+0800'
        format_created = timezone.datetime.strptime(
            created, '%b %d, %Y %I:%M%p-%z')

        author = headers.find_element_by_class_name('author').text
        author = User.objects.filter(full_name=author).first()

        title = driver.find_element_by_class_name(
            'detail-page-description').find_element_by_class_name(
            'title-container').text

        sidebar = driver.find_element_by_class_name('issuable-context-form')
        try:
            assignee = sidebar.find_element_by_class_name(
                'username').text.replace('@', '')
            assignee = User.objects.filter(username=assignee).first()
        except Exception as e:
            assignee = None

        try:
            milestone = sidebar.find_element_by_class_name(
                'milestone').find_element_by_class_name('value').text
            milestone = Milestone.objects.filter(name=milestone).first()
        except Exception as e:
            milestone = None

        try:
            labels = sidebar.find_element_by_class_name(
                'issuable-show-labels').find_elements_by_tag_name('span')
            label_list = []
            for label in labels:
                label_list.append(label.text)
        except Exception as e:
            label_list = []
        contents = {
            'status': status,
            'created': format_created,
            'author': author,
            'title': title,
            'assignee': assignee,
            'milestone': milestone,
            'number': num,
        }
        issue, msg = Issue.objects.update_or_create(
            number=num,
            project=project,
            defaults=contents)

        if label_list:
            # Remove all labels before updating labels
            issue.labels.clear()
            labels = Label.objects.filter(name__in=label_list, project=project)
            if labels.exists():
                issue.labels.add(*labels)

        fetch_timeline_info(driver, issue)

    except Exception as e:
        print('WARNING: Failed in #{}'.format(num))


def update_issue_infos(index):
    driver = webdriver.Chrome()
    driver.get(settings.SITE_URL)
    driver.maximize_window()
    driver = webdriver_login(
        driver, settings.USERNAME, settings.PASSWORD)
    projects = Project.objects.filter(name__in=settings.REPO_NAME)
    for project in projects:
        url = settings.SITE_URL + '/{}/issues'.format(project.repo_name)
        driver.get(url)
        issue_count = driver.find_element_by_id(
            'state-all').find_element_by_class_name(
            'badge').text.replace(',', '')

        start_index = int(issue_count) - index
        start_index = 1 if start_index < 1 or index >= 999 else start_index
        for i in range(start_index, int(issue_count) + 1):
            issue_url = '{}/{}'.format(url, i)
            fetch_issue_detail_info(driver, issue_url, i, project)
    driver.quit()
    return True


def generate_csv_file(issues, file_name):
    csv_readers = [
        'Issue', 'Title', 'Status', 'Author', 'Assignee', 'Started', 'Closed',
        'Time Spent', 'Participation', 'Project', 'Milestone', 'Labels']
    c_file = open(
        "{}{}".format(settings.DOWNLOAD_PATH, file_name), "w")
    search_file = csv.writer(c_file)
    search_file.writerow(csv_readers)

    for issue in issues:
        assignee = issue.assignee.username if issue.assignee else ''
        milestone = issue.milestone.name if issue.milestone else ''
        issue_row = [
            issue.number, issue.title, issue.status_display,
            issue.author.username, assignee,
            issue.started_string, issue.closed_string,
            issue.time_spent_label, issue.participation_string_with_time,
            issue.project.repo_name, milestone, issue.labels_string
        ]
        search_file.writerow(issue_row)

    c_file.close()


def update_issue_time_infos():
    closed_issues = Issue.objects.select_related('project').filter(
        status=Issue.CLOSED, project__name__in=settings.REPO_NAME)
    for issue in closed_issues:
        issue.started = issue.started_datetime
        issue.closed = issue.closed_datetime
        issue.save(update_fields=['started', 'closed'])

        doing_actions = issue.actions.filter(
            action__icontains='added Doing').order_by('when')
        for action in doing_actions:
            if issue.assignee != action.owner:
                if action.owner not in issue.participants.all():
                    issue.participants.add(action.owner)
    return True
