#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
'''
https://doi.org/10.1175/JCLI-D-23-0635.1
First, the nonbandpass filtering method proposed by Hsu et al. (2015) 
is applied to obtain the intraseasonal (20–70 days) component of
both hindcasts and observations. This method may efficiently extract
the intraseasonal components without losing much boundary data. The 
specific procedures are as follows. After removing the annual cycle 
(daily climatology) from the raw data, the mean of the previous 35 days 
was subtracted from the anomalous field to further remove the lower-
frequency (>70 days) component. Then the preceding 10-day mean is applied
to remove the higher-frequency (<20 days) component. Note that the past
43 days of observed data have been prepended to each hindcast.

Second, the MJO events active over the eastern Indian Ocean (EIO) 
during boreal winters (from November to April) are selected for analysis. 
When OLR anomaly averaged over equatorial EIO (10°S–10°N, 75°–95°E) is 
less than one negative standard deviation for at least five consecutive 
days, it is chosen as one event, and day 0 is defined as the date with the
minimum OLR anomaly (B. Wang et al. 2019). A total of 57 MJO events are 
identified during 1999–2019.
'''
import pytools.nctools as nct
import pytools.timetools as tt
import numpy as np
import os


def main():
    areaName, areaBounds = 'EIO1', [75, 95, -10, 10]
    midPath, desPath = calOlrAnom(areaName, areaBounds)

    # ---- read olr anomaly
    dateMinMax = [tt.ymd2float(2001, 1, 1), tt.ymd2float(2024, 3, 31)]
    dateReadRange = dateMinMax.copy()
    dateReadRange[0] -= 35 + 10

    olr, dims = nct.ncreadByDimRange(midPath, 'olr', [dateReadRange])
    dates = dims[0]
    numDates = len(dates)

    # ---- fill the missing values
    imiss = np.where(np.abs(olr)>1E10)[0]
    print(f' missing dates: {', '.join([tt.float2format(d) for d in dates[imiss]])}')
    olr[imiss] = (olr[imiss-1] + olr[imiss+1]) * 0.5

    # ---- minus the previous 35 day mean
    olrPrev35 = np.nan * np.ones((numDates))
    num35 = 35
    for i in range(numDates):
        if i < num35:
            continue
        olrPrev35[i] = olr[i] - np.nanmean(olr[i-num35:i])
    
    # --- apply 10 day mean
    num10 = 10
    olrFiltered = np.nan * np.ones((numDates))
    for i in range(numDates):
        if i < num35 + num10:
            continue
        olrFiltered[i] = np.nanmean(olrPrev35[int(i-num10/2):int(i+num10/2)])

    std = np.nanstd(olrFiltered)
    eventsDates = [] # -> reference date for the minimum OLR anomaly.
    wasInEvent = False
    for date, olr in zip(dates, olrFiltered):
        if olr > -std and not wasInEvent: # inactive
            continue

        if olr > -std and wasInEvent: # event ends
            wasInEvent = False
            if len(eventDates) >= 5: # must last >= 5 days
                iday = np.argmin(eventOlrs)
                eventsDates.append(eventDates[iday])
            continue

        if olr <= std and not wasInEvent: # event begins
            wasInEvent = True
            eventDates = [date]
            eventOlrs = [olr]
            continue

        if olr <= std and wasInEvent: # event continues
            wasInEvent = True
            eventDates.append(date)
            eventOlrs.append(olr)
            continue

    # ---- print dates for output
    eventsDatesJan = [d for d in eventsDates if tt.month(d) == 1]
    print(f' std of all-season OLR = {std}')
    print(f' number of events = {len(eventsDates)}:')
    print([tt.float2format(d) for d in eventsDates])
    print(f' number of events in January = {len(eventsDatesJan)} :')
    print([tt.float2format(d) for d in eventsDatesJan])

    print(f'{desPath = }')
    if os.path.exists(desPath):
        os.remove(desPath)
    nct.save(desPath, {'date': eventsDates}, overwrite=True)
    

def calOlrAnom(areaName, areaBounds):
    srcRoot = '/nwpr/gfs/com120/9_data/NOAA_OLR'
    pathTotal = f'{srcRoot}/olr.cbo-1deg.day.mean.nc'
    pathClim = f'{srcRoot}/olr_clim_2001_2020_1p0_5dma.nc'
    pathOut = f'../../data/MJO/areaMeanOlr/{areaName}-c2001-2020-5dma_olr.nc'
    pathDes = f'../../data/MJO/areaMeanOlr/{areaName}-c2001-2020-5dma_caseDates.nc'
    strAreaBounds=','.join([str(ab) for ab in areaBounds])

    if os.path.exists(pathOut):
        return pathOut, pathDes

    cmd = f'cdo --reduce_dim -P 8 -f nc4 -z zip9'
    cmd += f' ydaysub'

    cmd += f' -fldmean -sellonlatbox,{strAreaBounds}'
    cmd += f' {pathTotal}'

    cmd += f' -fldmean -sellonlatbox,{strAreaBounds}'
    cmd += f' {pathClim}'

    cmd += f' {pathOut}'
    os.system(cmd)
    return pathOut, pathDes


if __name__ == '__main__':
    main()
