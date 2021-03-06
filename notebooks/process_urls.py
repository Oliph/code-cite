import requests
import datetime
import process_zenodo
from github import Github


def is_url_valid(url):
    response = requests.get(url)
    return_code = response.status_code
    if return_code == 200:
        return True
    else:
        return False

    
def check_github_licence_exists(repo):
    possible_filenames = ['LICENCE', 'COPYING','LICENSE','LICENCE.md','LICENSE.md','LICENCE.TXT','LICENSE.TXT']
    for content in repo.get_contents('/'):
        name = content.name
        for poss_name in possible_filenames:
            if poss_name in name.upper():
                return True
    return False

def check_github_readme_exists(repo):
    possible_filenames = ['README', 'README.md','README.TXT','README.rst']
    for content in repo.get_contents('/'):
        name = content.name
        for poss_name in possible_filenames:
            if poss_name in name.upper():
                return True
    return False

    
def validate_github_licence(url,token):  
    git_url_suffix = (url.split('github.com/'))[1]
    #git_url_split = (git_url_suffix.split('/'))
    #git_url_path = git_url_split[0]+'/'+git_url_split[1]
    g = Github(token)                 
    repo = g.get_repo(git_url_suffix)
    licence_exists = check_github_licence_exists(repo)
    return licence_exists

def validate_github_readme(url,token):  
    git_url_suffix = (url.split('github.com/'))[1]
    #git_url_split = (git_url_suffix.split('/'))
    #git_url_path = git_url_split[0]+'/'+git_url_split[1]
    g = Github(token)                 
    repo = g.get_repo(git_url_suffix)
    readme_exists = check_github_readme_exists(repo)
    return readme_exists

def process_github_url(url, doi, verbose=False, github_token=None):
    """
    Given a github URL, calculate a 'code score' and report attributes
    
    A string, 'url', found in a paper, represented by 'doi', is processed
    to establish if the URL resolves, and if it does check for attributes of
    the repository that may be an indicator of code quality.
    """
    url_dict = {'doi': doi,
                'url': url,
                'resourcetype': 'github',
                'timestamp': datetime.datetime.now().isoformat(),
                'resolves': None,
                'score': 0,
                'licence_exists': None}

    if not is_url_valid(url):
        url_dict['resolves'] = False
        if verbose: print("URL {} did not resolve".format(url))
        return url_dict
    
    url_dict['resolves'] = True
    url_dict['score'] = url_dict['score'] + 1

    if verbose: print("check licence for URL {}".format(url))

    # Skip non-repo URLs
    if 'blob' in url:
        if verbose: 
            print("skipping licence check for URL {}".format(url))
        return url_dict
        
    if github_token is not None:
        try:
            licence_exists = validate_github_licence(url, github_token)
        except Exception as e:
            if verbose: print("Exception {} when checking for licence".format(e))
            licence_exists = False
           
        url_dict['licence_exists'] = licence_exists
        if licence_exists:
            print("URL {} has a licence".format(url))
            url_dict['score'] = url_dict['score'] + 1
        else:
            print("URL {} does not have a licence".format(url))
            
        try:
            readme_exists = validate_github_readme(url, github_token)
        except Exception as e:
            if verbose: print("Exception {} when checking for readme".format(e))
            readme_exists = False
           
        url_dict['readme_exists'] = readme_exists
        if readme_exists:
            print("URL {} has a readme".format(url))
            url_dict['score'] = url_dict['score'] + 1
        else:
            print("URL {} does not have a readme".format(url))
            
    return url_dict


def process_zenodo_url(url, doi, verbose=False):
    """
    Given a zenodo URL, calculate a 'code score' and report attributes
    
    A string, 'url', found in a paper, represented by 'doi', is processed
    to establish if the URL resolves, and if it does check for attributes of
    the repository that may be an indicator of code quality.
    """
    url_dict = {'doi': doi,
                'url': url,
                'resourcetype': 'zenodo',
                'timestamp': datetime.datetime.now().isoformat(),
                'resolves': None,
                'score': 0,
                'licence_exists': None}

    if not is_url_valid(url):
        url_dict['resolves'] = False
        if verbose: print("URL {} did not resolve".format(url))
        return url_dict
    url_dict['resolves'] = True
    url_dict['score'] = url_dict['score'] + 1
            
    licence_exists = process_zenodo.check_zenodo_licence_exists(url)
    url_dict['licence_exists'] = licence_exists
    if licence_exists:
        print("URL {} has a licence".format(url))
        url_dict['score'] = url_dict['score'] + 1
    else:
        print("URL {} does not have a licence".format(url))
    
    return url_dict


def process_papers_dict(dict_of_papers, verbose=False, github_token=None):
    """
    For a list of papers (represented by dois) and URLs check each one
    
    """
    resources_list = []
    papers_output_dict = {}

    for paper_doi in dict_of_papers:
        paper = dict_of_papers[paper_doi]
        paper_score = 0
        number_or_resources = 1E-17
        
        if verbose: print("processing paper with doi {}".format(paper_doi))
        
        if 'github' in paper:
            for url in paper['github']:
                url_dict = process_github_url(url, paper_doi, verbose=verbose,
                                             github_token=github_token)
                paper_score = paper_score + url_dict['score']
                number_or_resources = number_or_resources + 1
                if 'pub_date' in paper:
                    url_dict['pub_date'] = paper['pub_date']
                resources_list.append(url_dict)
            
        if 'zenodo' in paper:
            for url in paper['zenodo']:
                url_dict = process_zenodo_url(url, paper_doi, verbose=verbose)
                paper_score = paper_score + url_dict['score']
                number_or_resources = number_or_resources + 1
                if 'pub_date' in paper:
                    url_dict['pub_date'] = paper['pub_date']
                resources_list.append(url_dict)
                    
            
        papers_output_dict[paper_doi] = {'score': paper_score, 
                                         'timestamp': datetime.datetime.now().isoformat()}
    
            
        if verbose: print("Paper with doi {} has score of {}".format(paper_doi, 
                                                     paper_score / number_or_resources))
            
    return resources_list
