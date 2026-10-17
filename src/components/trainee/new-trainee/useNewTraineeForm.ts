import { useEffect, useMemo, useState } from "react";
import { useRouter } from "expo-router";
import { Alert } from "react-native";

import { MasterGroup, fetchTrainers, fetchZones } from "@/api/training";
import { SelectOption } from "@/components/ui/SearchableSelect";
import type { PickedImage } from "@/api/auth";
import { ApiError, registerNewTrainee, uploadNewTraineePhoto } from "@/api/trainee";
import { useAuth } from "@/hooks/useAuth";
import { useStateDistricts } from "@/hooks/useStateDistricts";
import { formatDate } from "@/components/training/add-training/formatting";
import {
  cleanText,
  companyId,
  digitsOnly,
  email,
  firstError,
  mobile10,
  normalizeEmail,
  pincode6,
  plausibleDob,
  required,
} from "@/utils/validation";

const randomDigits = (length: number) =>
  Array.from({ length }, () => Math.floor(Math.random() * 10)).join("");

const generatePassword = () => `TRN${randomDigits(4)}@${new Date().getFullYear()}`;

export function useNewTraineeForm() {
  const router = useRouter();
  const { adminToken, adminLogout } = useAuth();

  // Corporate Mapping
  const [zone, setZone] = useState("");
  const [region, setRegion] = useState("");
  const [company, setCompany] = useState("Samsung India");
  const [requestedByOption, setRequestedByOption] = useState("");
  const [requestedByOther, setRequestedByOther] = useState("");
  const requestedBy = requestedByOption === "Other" ? requestedByOther : requestedByOption;

  // Leadership Context
  const [trainerId, setTrainerId] = useState("");
  const [trainerName, setTrainerName] = useState("");
  const [supervisorId, setSupervisorId] = useState("");
  const [supervisorName, setSupervisorName] = useState("");
  const [supervisorDesignation, setSupervisorDesignation] = useState("");

  // Zone / Region come from the master list: the zones, each with its regions (/admin/zones).
  const [zoneGroups, setZoneGroups] = useState<MasterGroup[]>([]);
  useEffect(() => {
    if (!adminToken) return;
    fetchZones(adminToken)
      .then(setZoneGroups)
      .catch(() => setZoneGroups([]));
  }, [adminToken]);
  const zoneOptions = useMemo(() => zoneGroups.map((group) => ({ label: group.name, value: group.name })), [zoneGroups]);
  const regionOptions = useMemo(
    () => (zoneGroups.find((group) => group.name === zone)?.options ?? []).map((name) => ({ label: name, value: name })),
    [zoneGroups, zone],
  );

  // Trainer / Supervisor pickers list this company's agencyteam trainers,
  // fetched live and re-fetched whenever the company changes.
  const [trainerOptions, setTrainerOptions] = useState<SelectOption[]>([]);
  useEffect(() => {
    if (!adminToken || !company) return;
    fetchTrainers(adminToken, company)
      .then(setTrainerOptions)
      .catch(() => setTrainerOptions([]));
  }, [adminToken, company]);

  const changeCompany = (value: string) => {
    setCompany(value);
    setTrainerId("");
    setTrainerName("");
    setSupervisorId("");
    setSupervisorName("");
  };

  // Trainee Profile
  const [profilePhoto, setProfilePhoto] = useState<PickedImage | null>(null);
  const [agencyId, setAgencyId] = useState("");
  const [fullName, setFullName] = useState("");
  const [designation, setDesignation] = useState("");
  const [gender, setGender] = useState("");
  const [dob, setDob] = useState("");

  // Contact Info
  const [primaryEmail, setPrimaryEmail] = useState("");
  const [primaryPhone, setPrimaryPhone] = useState("");
  const [altEmail, setAltEmail] = useState("");
  const [altPhone, setAltPhone] = useState("");
  const [address, setAddress] = useState("");
  const [stateValue, setStateValue] = useState("");
  const [district, setDistrict] = useState("");
  // State / District from the pincode directory; the District options are the chosen state's.
  const { stateOptions, districtOptions } = useStateDistricts(stateValue, district);

  // Employment Details
  const [joinedOn, setJoinedOn] = useState(() => formatDate(new Date()));
  const [jobStatus, setJobStatus] = useState("Active");
  const [jobCity, setJobCity] = useState("");
  const [jobPincode, setJobPincode] = useState("");
  const [resignedOn, setResignedOn] = useState("");

  // System Access
  const [password] = useState(generatePassword);
  const [verified, setVerified] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const changeJobStatus = (value: string) => {
    setJobStatus(value);
    if (value !== "Resigned") setResignedOn("");
  };

  const handleSubmit = async () => {
    const missingRequired = firstError(
      required(zone), required(region), required(company), required(requestedBy),
      required(trainerId), required(supervisorId),
      required(fullName), required(designation), required(gender),
      required(primaryEmail), required(primaryPhone),
      required(stateValue), required(district),
    );
    if (missingRequired) {
      setNotice("Please fill in all required (*) fields.");
      return;
    }
    const formatError = firstError(
      email(primaryEmail, "Primary email"),
      email(altEmail, "Alt email"),
      mobile10(primaryPhone, "Primary phone"),
      mobile10(altPhone, "Alt phone"),
      pincode6(jobPincode, "Job pincode"),
      companyId(agencyId, "Agency/Company ID"),
      plausibleDob(dob),
    );
    if (formatError) {
      setNotice(formatError);
      return;
    }
    if (!verified) {
      setNotice("Please verify that the information entered above is correct.");
      return;
    }
    if (!adminToken) {
      setNotice("Your session has expired. Please log in again.");
      return;
    }

    setSubmitting(true);
    setNotice(null);
    try {
      const created = await registerNewTrainee(adminToken, {
        profilePhoto: null, // the photo itself is uploaded below, once the trainee exists
        agencyId: agencyId || null,
        fullName: cleanText(fullName, 120),
        designation,
        gender,
        dob: dob || null,
        primaryEmail: normalizeEmail(primaryEmail),
        primaryPhone: digitsOnly(primaryPhone),
        altEmail: normalizeEmail(altEmail) || null,
        altPhone: digitsOnly(altPhone) || null,
        address: cleanText(address, 300) || null,
        state: stateValue,
        district,
        zone,
        region,
        company,
        requestedBy,
        trainerId,
        trainerName,
        supervisorId,
        supervisorName,
        supervisorDesignation: supervisorDesignation || null,
        joinedOn,
        jobStatus,
        jobCity: cleanText(jobCity, 80) || null,
        jobPincode: digitsOnly(jobPincode) || null,
        resignedOn: resignedOn || null,
        password,
      });

      let photoMissing = false;
      if (profilePhoto) {
        try {
          await uploadNewTraineePhoto(adminToken, created.traineeUid, profilePhoto);
        } catch {
          // The trainee is saved either way; only the photo is missing.
          photoMissing = true;
        }
      }

      // The server made the trainee's ID - their login ID - so it's shown once, with their password.
      Alert.alert(
        "Trainee added",
        `Trainee ID (login): ${created.traineeUid}\nPassword: ${password}` +
          (photoMissing ? "\n\nThe profile photo couldn't be uploaded. The trainee can add it from their own profile." : ""),
      );
      router.back();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        adminLogout();
        router.replace({ pathname: "/trainer_login", params: { reason: "session_expired" } });
        return;
      }
      setNotice(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return {
    zone, setZone,
    zoneOptions,
    region, setRegion,
    regionOptions,
    company, setCompany: changeCompany,
    requestedByOption, setRequestedByOption,
    requestedByOther, setRequestedByOther,
    requestedBy,

    trainerId, setTrainerId,
    trainerName, setTrainerName,
    supervisorId, setSupervisorId,
    supervisorName, setSupervisorName,
    supervisorDesignation, setSupervisorDesignation,
    trainerOptions,

    profilePhoto, setProfilePhoto,
    agencyId, setAgencyId,
    fullName, setFullName,
    designation, setDesignation,
    gender, setGender,
    dob, setDob,

    primaryEmail, setPrimaryEmail,
    primaryPhone, setPrimaryPhone,
    altEmail, setAltEmail,
    altPhone, setAltPhone,
    address, setAddress,
    stateValue, setStateValue,
    district, setDistrict,
    stateOptions,
    districtOptions,

    joinedOn, setJoinedOn,
    jobStatus, setJobStatus: changeJobStatus,
    jobCity, setJobCity,
    jobPincode, setJobPincode,
    resignedOn, setResignedOn,

    password,
    verified, setVerified,

    submitting, notice, handleSubmit,
  };
}

export type NewTraineeForm = ReturnType<typeof useNewTraineeForm>;
