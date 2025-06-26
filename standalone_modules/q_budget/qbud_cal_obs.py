#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools as pyt


def main():
    caseDate = pyt.tt.ymd2float(2009, 1, 26)
    numDates = 15
    areas = [70, 180, -15, 15]
    levelTop = 700

    timeRange = [caseDate, caseDate + numDates - 1]


# def read_total()



if __name__ == '__main__':
    main()
