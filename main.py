import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def setup():
    ''' performs basic setup for selenium to browse https://classsearch.nd.edu, returns driver '''
    options = Options()
    options.headless = True
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    dc = DesiredCapabilities.CHROME
    dc["goog:loggingPrefs"] = {"browser":"ALL"}
    driver = webdriver.Chrome(options=options, desired_capabilities=dc)
    driver.get('https://classsearch.nd.edu')
    driver.execute_script("document.getElementById('crit-srcdb').value='202220';")
    return driver

def menu():
    ''' displays menu, returns user selection (1-4) '''
    print('\nWhat would you like to do?')
    print('1: Add or update a class\n2: Remove a class\n3: View saved classes\n4: Exit')
    selection = int(input('\nMake a selection: '))

    if selection not in {1, 2, 3, 4}:
        print('Error: please enter a valid selection')
        time.sleep(1.5)
        menu()
    
    return selection

def search(driver):
    ''' prompts user to search for class, returns list with search results '''
    usr_class = input('\nWhat class do you want to take: ')
    driver.execute_script("document.getElementById('crit-keyword').value='" + usr_class + "';")
    driver.execute_script("document.getElementById('search-button').click();")
    driver.execute_script("await new Promise(r => setTimeout(r, 2000));")

    driver.execute_script("console.log(document.querySelectorAll('[data-key]').length);")
    data_text = driver.get_log('browser')[0]['message']
    num_classes = int(data_text[17:])
    results = []
    for i in range(1, num_classes):
        driver.execute_script("console.log(document.querySelectorAll('[data-key]')[" + str(i) + "].textContent);")
        data_text = driver.get_log('browser')[0]['message']
        results.append(data_text[17:].split("\\n")[1] + ': ' + data_text[17:].split("\\n")[2])
    return results


def search_results(driver, results):
    ''' displays all classes from search results, returns class based on user selection '''
    print('\nSearch Results:')
    for pos, course in enumerate(results, start=1):
        print(f'{pos}: {course}')
    print(f'{len(results)+1}: Back to search')
    course = input("\nWhat class you want to check: ")

    try:
        if int(course) == len(results)+1: 
            print()
            results = search()
            search_results(results)
        else:
            driver.execute_script("document.querySelectorAll('[data-key]')[" + course + "].click();")
            driver.execute_script("await new Promise(r => setTimeout(r, 2000));")
            return results[int(course)-1]
    except:
        print('\nError: must select a valid course')
        time.sleep(2)
        search_results(results)

def check_seats(driver):
    '''  displays the remaining seats in each section of class from search_results, returns section, crn, and remaining seats based on user selection '''
    print('\nSections:')
    driver.execute_script("console.log(document.getElementsByClassName(['course-section-all-sections-seats']).length);")
    data_text = driver.get_log('browser')[0]['message']
    num_sections = int(data_text[17:])

    seats_left = []
    for i in range(num_sections):
        driver.execute_script("console.log(document.getElementsByClassName(['course-section-all-sections-seats'])[" + str(i) + "].textContent);")
        data_text = driver.get_log('browser')[0]['message']
        seats_left.append(int(data_text[26:len(data_text) - 1]))
        print(f'Section {i+1}: {seats_left[i]} Seats')

    section = int(input("\nWhat section do you want to track: "))
    remaining_seats = seats_left[section-1]

    driver.execute_script("console.log(document.getElementsByClassName(['course-section-crn'])[" + str(section-1) + "].textContent);")
    data_text = driver.get_log('browser')[0]['message']
    crn = data_text[24:len(data_text)-1]

    return section, crn, remaining_seats

def update_file(driver, course, section, crn, remaining_seats):
    ''' updates classes.txt based on course, section, crn, and remaining seats parameters'''
    data_text = []
    open('classes.txt', 'a').close()
    with open('classes.txt', 'r') as fh:
        updated = False
        for line in fh.readlines():
            if crn in line:
                data_text.append(f'{course}, Section: {section}, CRN: {crn}, Seats: {remaining_seats}\n')
                updated = True
            else:
                data_text.append(line)
        if not updated:
            data_text.append(f'{course}, Section: {section}, CRN: {crn}, Seats: {remaining_seats}\n')
        
        if len(data_text) > 1:
            data_text[-2] += '\n'
        data_text[-1] = data_text[-1].rstrip()

    with open('classes.txt', 'w') as fh:
        fh.writelines(data_text)

    driver.execute_script("document.getElementsByClassName('fa fa-caret-left')[0].click();")

def main():
    ''' main execution '''
    driver = setup()

    done = False
    while not done:
        choice = menu()
        if choice == 1:
            results = search(driver)
            course = search_results(driver, results)
            section, crn, remaining_seats = check_seats(driver)
            update_file(driver, course, section, crn, remaining_seats)
        elif choice == 2:
            if os.path.exists('classes.txt'):
                openings = []
                with open('classes.txt', 'r') as fh:
                    lines = fh.readlines()
                print('\nClasses:')
                for pos, line in enumerate(lines, start=1):
                    print(f'{pos}: {line}')
                remove = int(input('\nSelect which class you want to remove: '))
                lines.pop(remove-1)
                with open('classes.txt', 'w') as fh:
                    fh.writelines(lines)
            else: 
                print('Error: you have not added any courses yet')
                time.sleep(1.5)
        elif choice == 3:
            if os.path.exists('classes.txt'):
                openings = []
                with open('classes.txt', 'r') as fh:
                    openings = fh.readlines()
                print(openings)
            else:
                print('Error: you have not added any courses yet')
                time.sleep(1.5)
        elif choice == 4:
            print('Goodbye!')
            done = True
    driver.quit()

if __name__ == '__main__':
    main()