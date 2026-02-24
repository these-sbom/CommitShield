import os
import re
import time
import requests
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from datetime import datetime, timezone

load_dotenv()

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']

class Git(ABC):
    @abstractmethod
    def get_commit_information(repo_url, rep):
        pass
    
    @abstractmethod
    def get_issues(message, rep):
        pass

    @abstractmethod
    def get_prs(message, rep):
        pass

    @abstractmethod
    def get_comment(comment_url):
        pass

    @abstractmethod
    def file_download(url, save_path):
        pass

class RemoteGit(Git):
    __number_of_requests_remaining_for_primary_rate_limit = 5000
    __time_at_which_primary_rate_limit_resets = 0

    def check_github_primary_rate_limit(self):
        if self.__number_of_requests_remaining_for_primary_rate_limit == 0:
            now = datetime.now(timezone.utc)
            time_to_wait = __time_at_which_primary_rate_limit_resets - now
            print('Wait (GitHub API primary rate limit) :', time_to_wait.seconds)
            time.sleep(time_to_wait.seconds)

    def set_github_primary_rate_limit(self, response_headers):
        self.__number_of_requests_remaining_for_primary_rate_limit = float(response_headers['x-ratelimit-remaining']) if ('x-ratelimit-remaining' in response_headers) else self.__number_of_requests_remaining_for_primary_rate_limit - 1
        if ('x-ratelimit-reset' in response_headers):
            __time_at_which_primary_rate_limit_resets = float(response_headers['x-ratelimit-reset'])
    
    def get_github_information_handling_primary_rate_limit(self, api_url, request_headers):
        self.check_github_primary_rate_limit()

        response = requests.get(api_url, headers=request_headers)

        self.set_github_primary_rate_limit(response.headers)
        
        return response
    
    def get_github_information_handling_rate_limits(self, api_url, request_headers):
        response = self.get_github_information_handling_primary_rate_limit(api_url, request_headers)

        if 'retry_after' in request_headers:
            time_to_wait_for_secondary_rate_limit = float(response.headers['retry_after'])
            if time_to_wait_for_secondary_rate_limit:
                print('Wait (GitHub API secondary rate limit) :', time_to_wait_for_secondary_rate_limit)
                time.sleep(time_to_wait_for_secondary_rate_limit)
                self.get_github_information_handling_primary_rate_limit(api_url, request_headers)

        return response

    def get_commit_information(self, repo_url, rep):
        response = self.get_github_information_handling_rate_limits(repo_url, {'Authorization': f'token {GITHUB_TOKEN}'})

        if response.status_code == 200:
            commit_info = response.json()
            commit = {}
            commit['sha'] = commit_info['sha']
            commit['message'] = commit_info['commit']['message']
            commit['url'] = commit_info['url']
            commit['status'] = commit_info['stats']
            commit['files'] = commit_info['files']
            commit['parents_commit'] = commit_info['parents'][0]['url']
            commit['parents_sha'] = commit_info['parents'][0]['sha']
            commit['comments_url'] = commit_info['comments_url']
            return commit
        else:
            print("Failed to get commit information:", response.status_code)
            return 0
    
    def get_issues(self, message, rep):
        match_obj = re.search(r'#(\d+)', message)
        if match_obj:
            number = match_obj.group(1)  
            issue_url = 'https://api.github.com/' + 'repos/' + rep.OWNER + '/' + rep.REPO + '/' + 'issues/' + number
            headers = {
                'Authorization': f'token {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = self.get_github_information_handling_rate_limits(issue_url, headers)

            if response.status_code == 200:
                issue_data = response.json()
                issue_description = issue_data.get('title', 'No description provided.')
                print("GET ISSUE!!!")
                return issue_description
            else:
                print(f'Failed to fetch issue: {response.status_code}')
                issue_description = 'NULL'
                return issue_description

    def get_prs(self, message, rep):
        match_obj = re.search(r'#(\d+)', message)
        if match_obj:
            number = match_obj.group(1)  
            pr_url = 'https://api.github.com/' + 'repos/' + rep.OWNER + '/' + rep.REPO + '/' + 'pulls/' + number
            headers = {
                    'Authorization': f'token {GITHUB_TOKEN}',
                    'Accept': 'application/vnd.github.v3+json'
                }
            
            response = self.get_github_information_handling_rate_limits(pr_url, headers)

            if response.status_code == 200:
                    pr_data = response.json()
                    pull_description =pr_data.get('body', 'No description provided.')
                    print("GET PULL REQUEST!!!")
                    return pull_description
            else:
                print(f'Failed to fetch pr: {response.status_code}')
                pr_description = 'NULL'
                return pr_description

    def get_comment(self, comment_url):
        url = comment_url
        headers = {
                'Authorization': f'token {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+json'
            }
        
        response = self.get_github_information_handling_rate_limits(url, headers)

        if response.status_code == 200:
            comment_data = response.json()
            if comment_data == '':
                comment_description = 'NULL'
                return comment_description
            else:
                comment_description = []
                for i in range(len(comment_data)):
                    comment_description.append(comment_data[i]['body'])
                return comment_description
        else:
            print(f'Failed to fetch issue: {response.status_code}')
            comment_description = 'NULL'
            return comment_description

    def file_download(self, url, save_path):
        headers = {
            "Authorization": GITHUB_TOKEN 
        }
        try:
            response = self.get_github_information_handling_rate_limits(url, headers)
            
            if response.status_code == 200:
            
                with open(save_path, 'wb') as file:
                    file.write(response.content)
            else:
                print(f"Failed: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
