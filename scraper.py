from bs4 import BeautifulSoup
import requests
import collections
import re

section_base_url = "https://man7.org/linux/man-pages/dir_section_{}.html"

# Define a function to extract command names and descriptions
def get_commands_from_section(section):
    url = section_base_url.format(section)
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        command_entries = soup.find_all('td', valign="top")

        posix_commands = []
        gnu_commands = []

        for entry in command_entries:
            commands_a = entry.find_all('a')
            for command in commands_a:
                if command != None:
                    text = command.text
                    if text == "intro(1)" or text == "intro(8)": #remove intro
                        continue
                    if "(1p)" in text: #posix
                        text = text.replace("(1p)", "")
                        posix_commands.append(text)
                    elif "(1)" in text:
                        text = text.replace("(1)", "")
                        gnu_commands.append(text)
                    elif "(8)" in text:
                        text = text.replace("(8)", "")
                        gnu_commands.append(text)

        # If a command is in both posix page and gnu page , remove the posix one
        same_commands = list(set(posix_commands).intersection(gnu_commands))
        posix_commands = [i for i in posix_commands if i not in same_commands] 

        posix_commands.sort()
        gnu_commands.sort()

        all_commands = posix_commands + gnu_commands

        return [posix_commands, gnu_commands, all_commands]

    else:
        print(f"Failed to fetch section {section}. Status code: {response.status_code}")
        return None

section1_commands = get_commands_from_section(1)
section8_commands = get_commands_from_section(8)

#remove tcpdump in section8
same_commands = list(set(section1_commands[2]).intersection(section8_commands[2]))
for i in [0, 1, 2]:
    section8_commands[i] = [j for j in section8_commands[i] if j not in same_commands]

print(f"Section1: {len(section1_commands[2])}\n")
print(f"Section8: {len(section8_commands[2])}\n")
print(f"Section1 + Section8: {len(section1_commands[2]) + len(section8_commands[2])}\n")

import json

man_page_posix_url = "https://man7.org/linux/man-pages/man{}/{}.{}p.html"
man_page_gnu_url = "https://man7.org/linux/man-pages/man{}/{}.{}.html"

def get_command_description_from_command(section, command, is_posix):
    if is_posix:
        url = man_page_posix_url.format(section, command, section)
    else:
        url = man_page_gnu_url.format(section, command, section)
    while True:
        try:
            response = requests.get(url)
        except:
            continue
        break

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        name_a = soup.find('a', id="NAME")
        name = None
        if name_a is not None:
            name_h2 = name_a.parent
            name = name_h2.findNext('pre').text
            name = name.strip()
            name = name.replace("\n", "")
            name = re.sub(r"([\n])|([\ ]{2,})", "", name)


        description = None
        description_a = soup.find('a', id="DESCRIPTION")
        if description_a is not None:
            description_h2 = description_a.parent
            description = description_h2.findNext('pre').text
            description = description.strip()
            description = re.sub(r"([\n])|([\ ]{2,})", "", description)


        return {'name':name, 'description':description}

    else:
        print(f"Failed to fetch command {command}. Status code: {response.status_code}")
        return None

def get_descriptions(section, commands, is_posix):
    command_list = []
    for command in commands:
        print(f'current fetch command: {command}\n')
        result = get_command_description_from_command(section, command, is_posix)
        if result != None:
            result['command'] = command
            result['section'] = section
            command_list.append(result)
    return command_list

res1 = get_descriptions(1, section1_commands[0], True)
res2 = get_descriptions(1, section1_commands[1], False)
res3 = get_descriptions(8, section8_commands[0], True)
res4 = get_descriptions(8, section8_commands[1], False)

res = res1+res2+res3+res4
json = json.dumps(res, sort_keys=True, indent=4)
print(json)

f = open("result.json", "w+")
f.write(json)
f.close()