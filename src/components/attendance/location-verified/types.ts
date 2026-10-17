export type LocationVerifiedInfo = {
  sessionTitle: string;
  sessionTime: string;
  date: string;
  location: string;
  verifiedTime?: string;
  venueLabel?: string;
  distanceLabel?: string;
  /** The trainee's own GPS position, reverse-geocoded on-device - shown
   *  alongside the venue's configured address so they can see it's really
   *  their current location that got verified, not just a repeated label. */
  liveLocation?: string;
};
