from astropy.coordinates import AltAz, SkyCoord, get_body
from astropy.time import Time
from time import sleep
from astropy import units

class AntennaTracking:
    def __init__(self, antenna_control):
        self.is_tracking = False
        self.antenna_control = antenna_control

    def track_object(self, antenna_location, object):
        print(f"{'Siguiendo '} {object}")
        while self.is_tracking:
            now = Time.now()
            altaz_frame = AltAz(obstime=now, location=antenna_location)
            tracked_object = get_body(object, now, antenna_location)
            tracked_object_altaz = tracked_object.transform_to(altaz_frame)
            az = tracked_object_altaz.az.deg
            el = tracked_object_altaz.alt.deg
            self.antenna_control.set_position(az, el)
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
            self.antenna_control.set_position(az, alt)
            sleep(1)