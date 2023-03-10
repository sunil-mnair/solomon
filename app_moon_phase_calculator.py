from datetime import datetime,timedelta

def converttojulian (D,M,Y):
    # The Julian Date value is calculated for the given day, month and year using the following steps
    A = Y / 100
    B = A / 4
    C = 2 - A + B
    E = 365.25 * (Y + 4716)
    F = 30.6001 * (M + 1)
    JD = C + D + E + F - 1524.5
    # since no time has been specified, the JD variable is modified to show exactly 00:00 on the specified date
    return(int(JD) + 0.5)

def datetophase(D,M,Y):
    JD = converttojulian(D,M,Y)
    dayssince = JD - 28.4766799998
    #Here the number starting with 28 is the julian date of the Earliest New Moon in Julian Dates
    numberofnewmoons = dayssince / 29.53

    #This determines the Julian Date of the last new moon before the specified date
    #Using that date, it determines the dates of the rest of the stages.
    lastnewmoon = ((int(numberofnewmoons)) * 29.53) + 28.4766799998
    fullmoon = lastnewmoon + 14.765
    firstquarter = (lastnewmoon + 7.3825)
    thirdquarter = (lastnewmoon + 22.1475)
    nextnewmoon = lastnewmoon + 29.53


    #These if statements determine if any of the 4 phases occurs on any the date specified.
    if (lastnewmoon >= JD and lastnewmoon < (JD + 1))or(nextnewmoon >= JD and nextnewmoon < (JD + 1)):
        return ('new moon'.title(),'https://github.com/prateetisaran/Moonphasecalculator/raw/master/newmoon.png')
    elif firstquarter >= JD and firstquarter < (JD + 1):
        return ('first quarter'.title(),'https://github.com/prateetisaran/Moonphasecalculator/raw/master/firstquarter.png')
    elif fullmoon >= JD and fullmoon < (JD + 1):
        return ('full moon'.title(),'https://github.com/prateetisaran/Moonphasecalculator/raw/master/fullmoon.png')
    elif thirdquarter >= JD and thirdquarter < (JD + 1):
        return ('third quarter'.title(),'https://github.com/prateetisaran/Moonphasecalculator/raw/master/thirdquarter.png')
    #If any of those 4 phases do not occur on this date, these if statements determine what phases this date is in between
    elif lastnewmoon < JD and firstquarter >= (JD + 1):
        return ('waxing crescent'.title(),'https://github.com/prateetisaran/Moonphasecalculator/raw/master/waxingcrescent.png')
    elif firstquarter < JD and fullmoon >= (JD + 1):
        return ('waxing gibbous'.title(),'https://github.com/prateetisaran/Moonphasecalculator/raw/master/waxinggibbous.png')
    elif fullmoon < JD and thirdquarter >= (JD + 1):
        return ('waning gibbous'.title(),'https://github.com/prateetisaran/Moonphasecalculator/raw/master/waninggibbous.png')
    elif thirdquarter < JD:
        return ('waning crescent'.title(),'https://github.com/prateetisaran/Moonphasecalculator/raw/master/waningcrescent.png')


def specificdate(x):
    #These get the date entered by the user and split it into 3 seperate values to be used for the calculation.

    specificdate = datetime.strptime(x,"%Y-%m-%d")
    specificdate = specificdate.strftime('%d %B %Y')

    Y = int(x[0:4])
    M = int(x[5:7])
    D = int(x[8:])

    moon_phase = datetophase(D,M,Y)

    return moon_phase,specificdate

    # toprint.set(moon_phase)

    # #These set up the corresponding image to be displayed based on the value obtained by the calculations.
    # moon_phase = displayimage(moon_phase)
    # moon_phase = ImageTk.PhotoImage(Image.open(moon_phase))
    # imgLabel.configure(image=moon_phase)
    # imgLabel.photo = moon_phase


def nextphasefm():
    x = datetime.now()
    c = datetophase((int(x.strftime('%d'))), (int(x.strftime('%m'))), (int(x.strftime('%Y'))))
    D = int(x.strftime('%d'))
    M = int(x.strftime('%m'))
    Y = int(x.strftime('%Y'))
    JD = converttojulian(D,M,Y)
    dayssince = JD - 28.4766799998
    numberofnewmoons = dayssince / 29.53
    lastnewmoon = ((int(numberofnewmoons)) * 29.53) + 28.4766799998
    fullmoon = lastnewmoon + 14.765
    fullmoondate = fullmoon - JD

    if fullmoon > JD:
        fm = datetime.now() + timedelta(days=fullmoondate)
        fm = fm.strftime('%d %B %Y')

    elif fullmoon < JD:
        fm = datetime.now() + timedelta(days=fullmoondate) + timedelta(days=29.53)
        fm = fm.strftime('%d %B %Y')

    elif c[0] == 'Full Moon':
        fm = datetime.now()
        fm = fm.strftime('%d %B %Y')

    return fm

def nextphasenm():
    x = datetime.now()
    c = datetophase((int(x.strftime('%d'))), (int(x.strftime('%m'))), (int(x.strftime('%Y'))))
    D = int(x.strftime('%d'))
    M = int(x.strftime('%m'))
    Y = int(x.strftime('%Y'))
    JD = converttojulian(D,M,Y)
    dayssince = JD - 28.4766799998
    numberofnewmoons = dayssince / 29.53
    lastnewmoon = ((int(numberofnewmoons)) * 29.53) + 28.4766799998
    nextnewmoon = lastnewmoon + 29.53
    newmoondate = nextnewmoon - JD

    if c[0] == 'New Moon':
        nm = datetime.now()
        nm = nm.strftime('%d %B %Y')
    else:
        nm = datetime.now() + timedelta(days=newmoondate)
        nm = nm.strftime('%d %B %Y')

    return nm