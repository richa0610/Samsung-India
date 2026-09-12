import { useEffect, useMemo, useState } from "react";
import { useRouter } from "expo-router";

import { fetchTrainers } from "@/api/training";
import { SelectOption } from "@/components/ui/SearchableSelect";
import { ApiError, registerNewTrainee } from "@/api/trainee";
import { STATES } from "@/data/states";
import { useAuth } from "@/hooks/useAuth";
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
  const [profilePhoto, setProfilePhoto] = useState<string | null>(null);
  const [traineeUid, setTraineeUid] = useState("");
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
  const selectedState = useMemo(() => STATES.find((item) => item.value === stateValue), [stateValue]);

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
      required(trainerId), required(supervisorId), required(traineeUid),
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
      await registerNewTrainee(adminToken, {
        traineeUid: cleanText(traineeUid, 50),
        profilePhoto,
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
        username: cleanText(traineeUid, 50),
        password,
      });

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
    region, setRegion,
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
    traineeUid, setTraineeUid,
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
    selectedState,

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
