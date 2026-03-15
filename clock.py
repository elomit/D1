"""
Work time analytics tool.

This programme is not to force employees to work more.
This programme should help to analyse how to make breaks more effectively.
It also should help to improve performance by adjusting working time (begin, end and timing of breaks).

Capture time:
python3 clock.py --clock_in --> clock in
python3 clock.py --break_start --> start of a break
etc.

In case you would like to correct something do:
python3 clock.py --correction

To get a quick report to see which factors correlatie with performance do:
python3 clock.py --report

Analyse and visualise:
See jupiter notebook.

"""


import sys
from datetime import datetime, timedelta
import argparse
import pandas as pd


# general to-dos and ideas
# TODO: Add visualisation output depending on arg, e.g. --plot
# TODO: Make function for every arg/column
# TODO: Use requirements.txt instead of imports
# TODO: Only calculate values for new entries and do not recalculate entire df
# TODO: Have additional_break time as separate column (for small breaks)
# TODO: Proper clean-up with pylint and flake8


# constants
PATH = 'clock_template.xlsx'
AVG_WORKDAY = 8


# get the current date and time
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
current_date = datetime.now().strftime('%Y-%m-%d')


# function to update  df and xlsx file
def update_clock(column_name, clock_df):
    """Add new data to clock.xlsx ."""
    # FIXME: Too many statements and branches

    # track times for clock_in, _out & break_start, _end
    # check if date exists
    if current_date in clock_df['date'].values:

        # handle different actions
        # start a break
        if column_name == 'break_start':

            # if break_start has no value yet, fill in empty value
            if pd.isna(clock_df.loc[len(clock_df)-1, column_name]):
                clock_df.loc[len(clock_df)-1, 'break_start'] = current_time

            # if it does not exist, work with break_start_n columns
            else:
                for n in range(2, 100):

                    # check whether break_start_n exists, if yes fill in current time there
                    if f'break_start_{n}' in clock_df.columns:
                        if pd.isna(clock_df.loc[len(clock_df)-1, f'break_start_{n}']):
                            clock_df.loc[len(clock_df)-1, f'break_start_{n}'] = current_time
                            break

                    # if it does not exist, create new column
                    else:
                        clock_df.loc[len(clock_df)-1, f'break_start_{n}'] = current_time
                        break

        # stop a break
        elif column_name == 'break_end':
            clock_df = calculate_break_time(clock_df)

            # save updated datafram
            clock_df.to_excel(PATH)

        # start work
        elif column_name == 'clock_in':
            print(f'I think I spider, you already did {column_name}. Exiting script.')
            sys.exit()

        # calculate extra hours worked when clocking out
        elif column_name == 'clock_out':
            print(clock_df.tail(5))

            # if it was clocked out already, exit script
            if pd.isna(clock_df.loc[len(clock_df)-1, column_name]):
                clock_df.loc[len(clock_df)-1, column_name] = current_time
            else:
                print(f'I think I spider, you already did {column_name}. Exiting script.')
                sys.exit()

            # calcualte worktime
            i = len(clock_df)-1  # FIXME: use df.last_valid_index
            clock_df, overall_extra_hours = calculate_work_time(clock_df, i)

            # calculate nr. of extra breaks
            extra_break_entries, break_df = get_extra_break_entries(clock_df)
            clock_df.loc[i, 'extra_breaks_count'] = extra_break_entries / 2

            # collect performance kpi
            print('Lief?')
            lief = input()
            clock_df.loc[len(clock_df)-1, 'lief'] = lief

            # homeoffice check
            print('Where did you work? (ho = home office, o = office, bib = bib, cowo = coworking, bib = library')
            print('For mixes write e.g. ho_cowo, meaning ho in the morning and cowo in the afternoon.')
            location = input()
            clock_df.loc[len(clock_df)-1, 'location'] = location

            if overall_extra_hours >= AVG_WORKDAY:
                print('Na nit hudle.')

            # end of week operations
            if datetime.now().weekday() == 4:

                # calculate weekly working hours
                last_week_hours = clock_df.iloc[-5:, :]['hours_worked'].sum()
                clock_df.loc[clock_df.index[-5:], 'week_hours'] = last_week_hours
                print(f'Stunden über die letzten 5 Arbeitstage: {round(last_week_hours,2)}')

                print('Willst du die Überstunden insgesamt wissen? (y/n)')
                extra_hours_answer = input()

                if extra_hours_answer == 'y':
                    print(f'Gesamte Überstunden: {round(overall_extra_hours, 2)}')

                print('Schönes Wochenende!')

    else:
        if column_name == 'clock_in':
            new_row = pd.DataFrame([{'date': current_date, column_name: current_time,
                                     'break_time': 0,
                                     'hours_worked': 0}])
            clock_df = pd.concat([clock_df, new_row], ignore_index=True)

            now = datetime.now()
            end_time = now + timedelta(hours=9)
            print(f'Current time: {now}')
            print(f'Get your shit done by {end_time}')

        else:
            print('Something went wrong.')
            print(f'Column: {column_name}')
            print(clock_df.tail())
            sys.exit()

    # save the updated DataFrame back to the xlsx file
    clock_df.to_excel(PATH)


def calculate_work_time(clock_df, i):
    """Calculate total hours and work hours."""
    i = len(clock_df)-1  # FIXME: use df.last_valid_index or similar
    try:
        clock_in_time = datetime.strptime(str(clock_df.loc[i, 'clock_in']), '%Y-%m-%d %H:%M:%S')
        clock_out_time = datetime.strptime(str(clock_df.loc[i, 'clock_out']), '%Y-%m-%d %H:%M:%S')
        total_work_time = clock_out_time - clock_in_time
        total_break_time = clock_df.loc[i, 'break_time'].sum()
        total_work_time -= timedelta(hours=total_break_time)
        hours_worked = total_work_time.total_seconds() / 3600

    except:  # FIXME: fix bare-except
        hours_worked = 0
        print('hours_worked for today was set to 0.')

    clock_df.loc[i, 'hours_worked'] = hours_worked

    # correct days where only performance was recorded
    # in this case clock_out is right after clock_out and we just assume a normal working day

    # calculate extra hours
    clock_df.loc[len(clock_df)-1, 'extra_hours'] = \
        clock_df.loc[len(clock_df)-1, 'hours_worked'] - AVG_WORKDAY
    overall_extra_hours = round(clock_df['extra_hours'].sum(), 2)


    return clock_df, overall_extra_hours


def calculate_break_time(clock_df):
    """Add breaks together and calculate total breaks time."""
    # if break ends, break time needs to be calculated
    additional_break_duration = 0

    # if break_end has no value yet, fill in empty value
    if pd.isna(clock_df.loc[len(clock_df)-1, 'break_end']):
        clock_df.loc[len(clock_df)-1, 'break_end'] = current_time
        break_start_time = datetime.strptime(
            str(clock_df.loc[len(clock_df)-1, 'break_start']), '%Y-%m-%d %H:%M:%S')
        break_end_time = datetime.strptime(
            str(clock_df.loc[len(clock_df)-1, 'break_end']), '%Y-%m-%d %H:%M:%S')
        break_duration = (break_end_time - break_start_time).total_seconds() / 3600
        clock_df.loc[len(clock_df)-1, 'break_time'] = break_duration

    # if it does not exist, work with break_end_n columns
    else:
        for n in range(2, 100):

            # check whether break_end_n exists, if yes fill in current time there
            if f'break_end_{n}' in clock_df.columns:
                if pd.isna(clock_df.loc[len(clock_df)-1, f'break_end_{n}']):
                    clock_df.loc[len(clock_df)-1, f'break_end_{n}'] = current_time

                    additional_break_duration = calculate_extra_break_time(
                        clock_df, additional_break_duration)

                    # when we filled value n, we can leave for loop
                    break

            # if it does not exist, create new column
            else:
                clock_df.loc[len(clock_df)-1, f'break_end_{n}'] = current_time
                additional_break_duration = calculate_extra_break_time(
                    clock_df, additional_break_duration)

                # when we added column with n, we can leave for loop
                break

    break_start_time = datetime.strptime(
        str(clock_df.loc[len(clock_df)-1, 'break_start']), '%Y-%m-%d %H:%M:%S')
    break_end_time = datetime.strptime(
        str(clock_df.loc[len(clock_df)-1, 'break_end']), '%Y-%m-%d %H:%M:%S')
    break_duration = (break_end_time - break_start_time).total_seconds() / 3600

    break_duration += additional_break_duration

    return clock_df


def get_extra_break_entries(clock_df):
    """Count the number of entries for extra breaks."""

    additional_break_list = \
        [column for column in clock_df.columns if column.count('_') > 1]  # FIXME: Better logic needed
    break_df = clock_df[additional_break_list]
    last_row = break_df.loc[len(break_df)-1]
    nr_extra_break_entries = len(last_row[~last_row.isna()])

    return nr_extra_break_entries, break_df


def calculate_extra_break_time(clock_df, additional_break_duration):
    """Calculate addtional break time."""

    nr_extra_break_entries, break_df = get_extra_break_entries(clock_df)

    for i in range(2, nr_extra_break_entries - 1):
        break_start_time = datetime.strptime(
            str(break_df.loc[len(break_df)-1, f'break_start_{i}']), '%Y-%m-%d %H:%M:%S')
        break_end_time = datetime.strptime(
            str(break_df.loc[len(break_df)-1, f'break_end_{i}']), '%Y-%m-%d %H:%M:%S')
        new_additional_break_duration = (break_end_time - break_start_time).total_seconds() / 3600
        additional_break_duration += new_additional_break_duration

    return additional_break_duration


def correction(clock_df):
    """Correct specific values."""
    # FIXME: only write HH:MM to correct times
    print(clock_df.tail())
    print('Which row?')
    row = int(input())
    print('Which column?')
    column = input()
    print('What is the new data? (format: YYYY-MM-DD HH:MM:SS)')
    new_data = input()

    clock_df.loc[row, column] = new_data
    if column == 'clock_out':

        # FIXME: Should be made function and should also include additional break time
        break_start_time = datetime.strptime(
            str(clock_df.loc[len(clock_df)-1, 'break_start']), '%Y-%m-%d %H:%M:%S')
        break_end_time = datetime.strptime(
            str(clock_df.loc[len(clock_df)-1, 'break_end']), '%Y-%m-%d %H:%M:%S')
        break_duration = (break_end_time - break_start_time).total_seconds() / 3600
        additional_break_duration = calculate_extra_break_time(clock_df, 0)
        break_duration += additional_break_duration
        clock_df.loc[len(clock_df)-1, 'break_time'] = break_duration

    elif 'break_end' in column:
        clock_df.loc[row, column] = new_data
        break_start_time = datetime.strptime(
            str(clock_df.loc[len(clock_df)-1, 'break_start']), '%Y-%m-%d %H:%M:%S')
        break_end_time = datetime.strptime(
            str(clock_df.loc[len(clock_df)-1, 'break_end']), '%Y-%m-%d %H:%M:%S')
        break_duration = (break_end_time - break_start_time).total_seconds() / 3600
        additional_break_duration = calculate_extra_break_time(clock_df, 0)
        break_duration += additional_break_duration

        clock_df.loc[len(clock_df)-1, 'break_time'] = break_duration

    calculate_work_time(clock_df, row)

    # save updated dataframe
    clock_df.to_excel(PATH)


def show(clock_df):
    """Show last 5 rows."""
    print(clock_df.iloc[:, :-3].tail())


def create_argparser():
    """Argument parser setup."""
    parser = argparse.ArgumentParser(description='Clock in/out script')
    parser.add_argument('--clock_in', action='store_true', help='Record clock in time')
    parser.add_argument('--clock_out', action='store_true', help='Record clock out time')
    parser.add_argument('--break_start', action='store_true', help='Record break start time')
    parser.add_argument('--break_end', action='store_true', help='Record break end time')
    parser.add_argument('--correction', action='store_true', help='correct previous input')
    parser.add_argument('--show', action='store_true', help='show last 5 rows')
    parser.add_argument('--report', action='store_true', help='analyse captured data')

    args = parser.parse_args()

    return args


def report(clock_df):
    """Calculate correlations"""

    # format starting and finishing hour into decimals
    clock_df['clock_out'] = pd.to_datetime(clock_df['clock_out'])
    clock_df['clock_in'] = pd.to_datetime(clock_df['clock_in'])

    for column in ['clock_in', 'clock_out']:
        clock_df[f'{column}_decimal'] = (
            clock_df[column].dt.hour
            + clock_df[column].dt.minute / 60
            + clock_df[column].dt.second / 3600
        )

    # one hot encoding
    clock_df = pd.get_dummies(clock_df, columns=["location"])
    clock_df["weekday"] = pd.to_datetime(clock_df["date"]).dt.day_name()
    clock_df = pd.get_dummies(clock_df, columns=["weekday"])

    # find correlations
    clock_df['days_count'] = clock_df.index
    numeric_df = clock_df.select_dtypes(include="number")
    corr_with_lief = numeric_df.corr()["lief"].sort_values(ascending=False)

    report = corr_with_lief.to_frame(name='')
    final_report = (
        report
            .dropna()
            .iloc[1:]
            .rename(index={
                'weekday_Monday': 'monday',
                'weekday_Tuesday': 'tuesday',
                'weekday_Wednesday': 'wednesday',
                'weekday_Thursday': 'thursday',
                'weekday_Friday': 'friday'
            })
)
    print('\nSee below the correlations with how the day went:')
    print(final_report, '\n')


def main():
    """Update the appropriate column based on the argument passed."""
    args = create_argparser()
    clock_df = pd.read_excel(PATH, index_col=0)
    time_cols = ["clock_in", "clock_out", "break_start", "break_end"]
    clock_df[time_cols] = clock_df[time_cols].apply(pd.to_datetime)
    # FIXME: check dtypes to avoid FutureWarning
    # see https://pandas.pydata.org/docs/whatsnew/v2.1.0.html#deprecations

    # format accidentally wrongly entered decimals
    clock_df['lief'] = (clock_df['lief'].astype(str).str.replace(',', '.', regex=False).astype(float))

    if args.clock_in:
        update_clock('clock_in', clock_df)
    elif args.clock_out:
        update_clock('clock_out', clock_df)
    elif args.break_start:
        update_clock('break_start', clock_df)
    elif args.break_end:
        update_clock('break_end', clock_df)
    elif args.correction:
        correction(clock_df)
    elif args.show:
        show(clock_df)
    elif args.report:
        report(clock_df)
    else:
        print('No valid argument provided. '
              'Use --clock_in, --clock_out, --break_start, --break_end, --show, --report or --correction.')


if __name__ == '__main__':
    main()
