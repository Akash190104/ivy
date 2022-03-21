import os
import re
import sys
import json


def command(cmd, save_output=True):
    if save_output:
        return json.loads(os.popen(cmd).read())
    else:
        os.system(cmd)


def carve_main_issue_body_functions(main_issue_body, allocated=True):
    if allocated:
        return [int(i[7:]) for i in main_issue_body.split('\r\n') if '- [ ] #' in i]
    return [i[6:] for i in main_issue_body.split('\r\n') if '#' not in i]


def main_issue_numbers(lst):
    x = []
    for number in lst:
        x.append(int(number['number']))
    return x


def issue_in_comment(cmt_bd):
    try:
        issue_id = re.search("[#/]\d+", cmt_bd)
        return True, issue_id.group(0)
    except AttributeError:
        return False, None


def comment_title(cid):
    x = command(f'gh issue view {int(cid[1:])} --json title')
    return x['title']


def functions_titles(issues_ids):
    return [command(f'gh issue view {issue_id} --json title')['title'] for issue_id in issues_ids]


issue_number = int(sys.argv[1])
comment_number = int(sys.argv[2])
comment_body = sys.argv[3]
comment_author = sys.argv[4]


main_issue_ids = main_issue_numbers(command('gh issue list --label "Array API","ToDo" --json number'))

if issue_number in main_issue_ids:
    main_issue = command(f'gh issue view {issue_number} --json number,title,body')
    alocate_functions = carve_main_issue_body_functions(main_issue['body'])
    non_alocate_functions = carve_main_issue_body_functions(main_issue['body'], False)
    issue_in_cmt, issue_id = issue_in_comment(comment_body)
    print(f"New comment detected on: '{main_issue['title']}'")
    print(f"Comment body: '{comment_body}'")

    if issue_in_cmt:
        comment_issue_id = int(issue_id[1:])
        comment_issue_title = comment_title(issue_id)
        if comment_issue_title in non_alocate_functions:
            print('Function Free')
            # ToDo: Add Labels "Array API" "Single Function"
            main_issue_body = main_issue['body'].replace(f'- [ ] {comment_issue_title}', f'- [ ] #{issue_id[1:]}')
            command(f'gh issue edit {comment_issue_id} --add-label "Array API","Single Function" --add-assignee "{comment_author}"', save_output=False)
            command(f'gh issue edit {main_issue["number"]} --body "{main_issue_body}"', save_output=False)
        elif (comment_issue_title not in non_alocate_functions) and (comment_issue_id not in alocate_functions):
            print('Function already allocated, closing issue.')
            command(f'gh issue comment {comment_issue_id} --body "This issue is being closed because the function has already been taken, please choose another function and recommend on the main issue."', save_output=False)
            command(f'gh issue close {comment_issue_id}', save_output=False)
        elif comment_issue_id in alocate_functions:
            print('Issue ID already in use...')
    else:
        # ToDo: Delete comment
        print('Deleting comment! No issue found.')
else:
    print('Skipping step')
