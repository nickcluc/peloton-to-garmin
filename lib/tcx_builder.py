import xml.etree.ElementTree as etree
from datetime import datetime, timezone
import logging

##############################
# Logging Setup
##############################

logger = logging.getLogger('peloton-to-garmin.Tcx_Builder')

METERS_PER_MILE = 1609.34

def getTimeStamp(timeInSeconds):
    timestamp = datetime.fromtimestamp(timeInSeconds, timezone.utc)
    iso = timestamp.isoformat()
    stepOne = iso.replace("+", ".")
    split = stepOne.split(":")
    return "{0}:{1}:{2}{3}Z".format(split[0],split[1],split[2],split[3])

def getHeartRate(heartRate):
    return "{0:.0f}".format(heartRate)

def getCadence(cadence):
    return "{0:.0f}".format(cadence)

def getSpeedInMetersPerSecond(speedInMilesPerHour):
    metersPerHour = speedInMilesPerHour * METERS_PER_MILE
    metersPerMinute = metersPerHour / 60
    metersPerSecond = round((metersPerMinute / 60), 2)
    return str(metersPerSecond)

def workoutSamplesToTCX(workout, workoutSummary, workoutSamples, outputDir):

    if(workoutSamples is None):
        logger.error("No workout sample data.")
        return

    startTimeInSeconds = workout['start_time']

    etree.register_namespace("","http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2")
    etree.register_namespace("activityExtensions", "http://www.garmin.com/xmlschemas/ActivityExtension/v2")

    root = etree.fromstring("""<TrainingCenterDatabase
  xsi:schemaLocation="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd"
  xmlns:ns3="http://www.garmin.com/xmlschemas/ActivityExtension/v2"
  xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ns4="http://www.garmin.com/xmlschemas/ProfileExtension/v1"></TrainingCenterDatabase>""")

    activities = etree.Element("Activities")

    activity = etree.Element("Activity")
    activity.attrib = dict(Sport="Biking")

    activityId = etree.Element("Id")
    activityId.text = getTimeStamp(startTimeInSeconds)

    lap = etree.Element("Lap")
    lap.attrib = dict(StartTime=getTimeStamp(startTimeInSeconds))

    intensity = etree.Element("Intensity")
    intensity.text = str("Active")

    totalTimeSeconds = etree.Element("TotalTimeSeconds")
    totalTimeSeconds.text = str(workout["peloton"]["ride"]["duration"])

    try:
        distanceMeters = etree.Element("DistanceMeters")
        miles = workoutSamples["summaries"][1]["value"]
        totalMeters = miles * METERS_PER_MILE
        distanceMeters.text = "{0:.1f}".format(totalMeters)
    except Exception as e:
            logger.error("Failed to Parse Distance - Exception: {}".format(e))
            return

    try:
        maximumSpeed = etree.Element("MaximumSpeed")
        maximumSpeed.text = getSpeedInMetersPerSecond(workoutSummary["max_speed"])

        calories = etree.Element("Calories")
        calories.text = str(int(round((workoutSummary["calories"]))))

        averageHeartRateBpm = etree.Element("AverageHeartRateBpm")
        ahrbValue = etree.Element("Value")
        ahrbValue.text = getHeartRate(workoutSummary["avg_heart_rate"])
        averageHeartRateBpm.append(ahrbValue)

        maximumHeartRateBpm = etree.Element("MaximumHeartRateBpm")
        mhrbValue = etree.Element("Value")
        mhrbValue.text = getHeartRate(workoutSummary["max_heart_rate"])
        maximumHeartRateBpm.append(mhrbValue)

        extensions = etree.Element("Extensions")
        lx = etree.Element("TPX")
        totalPower = etree.Element("TotalPower")
        totalPower.text = "{0:.2f}".format(workoutSummary["total_work"])
        avgSpeed = etree.Element("AverageSpeed")
        avgSpeed.text = getSpeedInMetersPerSecond(workoutSummary["avg_speed"])
        maxSpeed = etree.Element("MaximumSpeed")
        maxSpeed.text = getSpeedInMetersPerSecond(workoutSummary["max_speed"])
        avgBikeCadence = etree.Element("AverageCadence")
        avgBikeCadence.text = getCadence(workoutSummary["avg_cadence"])
        maxBikeCadence = etree.Element("MaximumCadence")
        maxBikeCadence.text = getCadence(workoutSummary["max_cadence"])
        avgBikeResistance = etree.Element("AverageResistance")
        avgBikeResistance.text = "{0:.2f}".format(workoutSummary["avg_resistance"])
        maxBikeResistance = etree.Element("MaximumResistance")
        maxBikeResistance.text = "{0:.2f}".format(workoutSummary["max_resistance"])
        avgWatts = etree.Element("AverageWatts")
        avgWatts.text = "{0:.2f}".format(workoutSummary["avg_power"])
        maxWatts = etree.Element("MaximumWatts")
        maxWatts.text = "{0:.2f}".format(workoutSummary["max_power"])
        lx.append(totalPower)
        lx.append(avgBikeCadence)
        lx.append(maxBikeCadence)
        lx.append(avgBikeResistance)
        lx.append(maxBikeResistance)
        lx.append(avgSpeed)
        lx.append(maxSpeed)
        lx.append(avgWatts)
        lx.append(maxWatts)
        extensions.append(lx)
    except Exception as e:

        logger.error("Failed to Parse Speed/Cal/HR - Exception: {}".format(e))
        return

    track = etree.Element("Track")

    metrics = workoutSamples["metrics"]
    heartRateMetrics = []
    outputMetrics = []
    cadenceMetrics = []
    speedMetrics = []

    if(metrics is None):
        logger.error("No workout metrics data.")
        return

    for item in metrics:
        if item["slug"] == "heart_rate":
            heartRateMetrics = item
        if item["slug"] == "output":
            outputMetrics = item
        if item["slug"] == "cadence":
            cadenceMetrics = item
        if item["slug"] == "speed":
            speedMetrics = item
        if item["slug"] == "resistance":
            resistanceMetrics = item

    seconds_since_start = workoutSamples["seconds_since_pedaling_start"]

    prevDist = 0
    for index, second in enumerate(seconds_since_start):
        trackPoint = etree.Element("Trackpoint")

        trackTime = etree.Element("Time")
        secondsSinceStart = second
        timeInSeconds = startTimeInSeconds + secondsSinceStart
        trackTime.text = getTimeStamp(timeInSeconds)
        trackPoint.append(trackTime)

        try:
            if heartRateMetrics:
                trackHeartRate = etree.Element("HeartRateBpm")
                thrValue = etree.Element("Value")
                thrValue.text = getHeartRate(heartRateMetrics["values"][index])
                trackHeartRate.append(thrValue)
                trackPoint.append(trackHeartRate)

        except Exception as e:
            logger.error("Exception: {}".format(e))

        try:
            if cadenceMetrics:
                trackCadence = etree.Element("Cadence")
                trackCadence.text = getCadence(cadenceMetrics["values"][index])
                trackPoint.append(trackCadence)
        except Exception as e:
            logger.error("Exception: {}".format(e))

        trackExtensions = etree.Element("Extensions")
        tpx = etree.Element("TPX")
        tpxSpeed = etree.Element("Speed")

        try:
            if speedMetrics:
                tpxSpeed.text = getSpeedInMetersPerSecond(speedMetrics["values"][index])
                tpx.append(tpxSpeed)
                tpxDistanceMeters = etree.Element("DistanceMeters")
                prevDist = prevDist + float(tpxSpeed.text)
                tpxDistanceMeters.text = str(prevDist)
                trackPoint.append(tpxDistanceMeters)
        except Exception as e:
            logger.error("Exception: {}".format(e))

        try:
            if outputMetrics:
                tpxWatts = etree.Element("Watts")
                tpxWatts.text = "{0:.0f}".format(outputMetrics["values"][index])
                tpx.append(tpxWatts)
        except Exception as e:
            logger.error("Exception: {}".format(e))

        try:
            if resistanceMetrics:
                tpxResistance = etree.Element("Resistance")
                tpxResistance.text = "{0:.0f}".format(resistanceMetrics["values"][index])
                tpx.append(tpxResistance)
        except Exception as e:
            logger.error("Exception: {}".format(e))

        trackExtensions.append(tpx)

        trackPoint.append(trackExtensions)

        track.append(trackPoint)

    lap.append(totalTimeSeconds)
    lap.append(distanceMeters)
    lap.append(maximumSpeed)
    lap.append(averageHeartRateBpm)
    lap.append(maximumHeartRateBpm)
    lap.append(calories)
    lap.append(intensity)
    lap.append(track)
    lap.append(extensions)

    activity.append(activityId)
    activity.append(lap)

    activities.append(activity)
    root.append(activities)
    tree = etree.ElementTree(root)

    instructor = ""
    if workout['peloton']['ride']['instructor'] is not None:
        instructor = " with " + workout['peloton']["ride"]["instructor"]["first_name"] + " " + workout['peloton']["ride"]["instructor"]["last_name"]

    cleanedTitle = workout["ride"]["title"].replace("/","-").replace(":","-")

    filename = "{0}-{1}{2}-{3}.tcx".format(startTimeInSeconds, cleanedTitle, instructor, workout['id'])
    outputDir = outputDir.replace("\"", "")
    tree.write("{0}/{1}".format(outputDir,filename), xml_declaration=True, encoding="UTF-8", method="xml")
