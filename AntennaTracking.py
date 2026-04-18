from astropy.coordinates import AltAz, SkyCoord, get_body
from astropy.time import Time
from time import sleep
from astropy import units

class AntennaTracking:
    def __init__(self, antenna_control):
        self.is_tracking = False
        self.antenna_control = antenna_control
        self.azimuth_offset = 0
        self.elevation_offset = 0

    def track_object(self, antenna_location, object):
        print(f"{'Siguiendo '} {object}")
        while self.is_tracking:
            now = Time.now()
            altaz_frame = AltAz(obstime=now, location=antenna_location)
            tracked_object = get_body(object, now, antenna_location)
            tracked_object_altaz = tracked_object.transform_to(altaz_frame)
            az = tracked_object_altaz.az.deg
            el = tracked_object_altaz.alt.deg
            self.antenna_control.set_position(az, el, False)
            sleep(1)

    def track_fixed_position(self, ra, dec, antenna_location):
        ra = float(ra.replace('−', '-'))
        dec = float(dec.replace('−', '-'))
        radec = SkyCoord(ra=ra*units.deg, dec=dec*units.deg, frame='icrs')
        print(f"{'Siguiendo las coordenadas RADEC'} {ra} {dec}")
        while self.is_tracking:
            now = Time.now()
            altaz_frame = AltAz(obstime=now,location=antenna_location)
            altaz = radec.transform_to(altaz_frame)
            alt = altaz.alt.deg
            az = altaz.az.deg
            self.antenna_control.set_position(az, alt, False)
            sleep(1)
    
    def pointing_calibration(self, antenna_location):
        object = "sun"
        print(f"{'Siguiendo '} {object}")
        while self.is_tracking:
            now = Time.now()
            altaz_frame = AltAz(obstime=now, location=antenna_location)
            tracked_object = get_body(object, now, antenna_location)
            tracked_object_altaz = tracked_object.transform_to(altaz_frame)
            az = float(round(tracked_object_altaz.az.deg, 1))
            el = float(round(tracked_object_altaz.alt.deg, 1))

            new_azimuth = float(round(az + self.azimuth_offset, 1))
            new_elevation = float(round(el + self.elevation_offset, 1))
            print(f"Offset: ({self.azimuth_offset},{self.elevation_offset}) Posición antena: ({new_azimuth},{new_elevation}) Posición sol: ({az}, {el})\r\n")
            self.antenna_control.set_position(new_azimuth, new_elevation, True)
            sleep(1)