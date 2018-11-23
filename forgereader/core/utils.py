# -*- coding: utf-8 -*-
import requests

from django.conf import settings

from bs4 import BeautifulSoup

from forgereader.core.models import ForgeUser, Milestone, Label


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


def resolve_url(state, assignee, author='', milestone='', label=''):
    repo_path = '/channelfix/channelfix'
    repo_url = settings.FORGE_URL + repo_path + '/issues?cope=all&utf8=%E2%9C%93&\
        state={}&assignee_username={}'.format(state, assignee)

    if author:
        repo_url += '&author_username={}'.format(author)
    if milestone:
        repo_url += '&milestone_title={}'.format(milestone)
    if label:
        repo_url += '&label_name[]={}'.format(label)
    return repo_url.replace(' ', '')


def fetch_issue_detail(issue):
    repo_path = '/channelfix/channelfix'
    repo_url = settings.FORGE_URL + repo_path + '/issues/{}'.format(issue)
    url = repo_url.replace(' ', '')
    html = sessions.get(url, headers=headers).text
    soup = BeautifulSoup(html, features="html.parser")

    try:
        milestone = soup.find(
            'div', class_="milestone").find('div', class_="value").find(
            'a', class_="bold").get_text().replace('\n', '')
    except Exception as e:
        milestone = ''

    print([milestone, ])


def fetch_user_issue_list(url):
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
            author = content.find('span', class_="author").get_text()
        except Exception as e:
            author = ''

        labels = []
        try:
            xlabels = content.findAll('a', class_="label-link")
            if xlabels:
                for label in xlabels:
                    labels.append(label.find('span').get_text())
        except Exception as e:
            labels = []

        # if link:
        #     detail_url = settings.FORGE_URL + link
        #     html0 = sessions.get(detail_url, headers=headers).text
        #     soup0 = BeautifulSoup(html0, features="html.parser")
        #     try:
        #         contents0 = soup0.find(
        #             'ul', class_="main-notes-list").findAll(
        #             'li', class_="timeline-entry")
        #         for content0 in contents0:
        #                 owner = content0.find(
        #                     'span',
        #                     class_="note-header-author-name").get_text()
        #                 action = content0.find(
        #                     'span', class_="system-note-message").find(
        #                     'span').get_text()
        #                 action_info = {
        #                     'owner': owner,
        #                     'action': action
        #                 }
        #     except Exception as e:
        #         action_info = {}

        print([number, title, author, labels])

        fetch_issue_detail(number)


def auto_run_forge():

    cs = Authentication(settings.FORGE_USERNAME, settings.FORGE_PASSWORD)
    cs.login()

    keywords = {
        'state': 'all',
        'assignee': 'chand.chen'
    }

    # state = input('状态(opened/closed/all): ')
    # if state:
    #     keywords['state'] = state
    # else:
    #     print('状态不能为空！')
    # assignee = input('被指派人(username): ')
    # if assignee:
    #     keywords['assignee'] = assignee
    # else:
    #     print('指派人不能为空！')
    # author = input('创建人(username): ')
    # if author:
    #     keywords['author'] = author
    # milestone = input('里程碑(空格用%20)： ')
    # if milestone:
    #     keywords['milestone'] = milestone
    # label = input('标签(Bug/空格用%20)： ')
    # if label:
    #     keywords['label'] = label

    url = resolve_url(**keywords)
    fetch_user_issue_list(url)


def update_milestone_data():
    cs = Authentication(settings.FORGE_USERNAME, settings.FORGE_PASSWORD)
    cs.login()

    repo_path = '/channelfix/channelfix'
    repo_url = settings.FORGE_URL + repo_path + '/milestones\
        ?sort=due_date_desc&state=all'
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
            Milestone.objects.get_or_create(
                name=name, defaults={
                    'name': name,
                    'milestone_range': milestone_range,
                    'status': status})


def update_label_data():
    cs = Authentication(settings.FORGE_USERNAME, settings.FORGE_PASSWORD)
    cs.login()

    repo_path = '/channelfix/channelfix'
    index_url = settings.FORGE_URL + repo_path + '/labels'
    html0 = sessions.get(index_url, headers=headers).text
    soup0 = BeautifulSoup(html0, features="html.parser")
    try:
        bottom = soup0.findAll(
            'li', class_="js-pagination-page")[-1].get_text().replace('\n', '')
    except Exception as e:
        bottom = 0
    for i in range(1, bottom):
        repo_url = settings.FORGE_URL + repo_path + '/labels?page={}'.format(i)
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
                Label.objects.get_or_create(
                    name=name, defaults={
                        'name': name,
                        'description': description
                    })


def update_forgeuser_data():
    cs = Authentication(settings.FORGE_USERNAME, settings.FORGE_PASSWORD)
    cs.login()

    repo_path = '/channelfix/channelfix'
    index_url = settings.FORGE_URL + repo_path + '/project_members'
    html0 = sessions.get(index_url, headers=headers).text
    soup0 = BeautifulSoup(html0, features="html.parser")
    try:
        bottom = soup0.findAll(
            'li', class_="js-pagination-page")[-1].get_text().replace('\n', '')
    except Exception as e:
        bottom = 0
    for i in range(1, int(bottom) + 1):
        repo_url = settings.FORGE_URL + repo_path + '/project_members?page\
            ={}'.format(i)
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
                ForgeUser.objects.get_or_create(
                    username=username, defaults={
                        'username': username,
                        'full_name': full_name
                    })
