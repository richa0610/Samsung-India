import { useEffect, useMemo, useState } from "react";
import { useRouter } from "expo-router";

import { SelectOption } from "@/components/ui/SearchableSelect";
import { STATES } from "@/data/states";
import { useAuth } from "@/hooks/useAuth";
import {
  ApiError,
  AssessmentSuiteOut,
  ModuleConfig,
  createTraining,
  fetchAssessmentSuites,
  fetchAudiences,
  fetchChecklistItems,
  fetchRequestedByOptions,
  fetchSessionTypes,
  fetchTrainers,
  fetchTrainingHubs,
  fetchTrainingTypes,
  fetchVenues,
} from "@/api/training";
import {
  DEFAULT_CATEGORY_OPTIONS,
  DEFAULT_QUESTION_SET_OPTIONS,
  MODULE_LABELS,
  ModuleKey,
} from "./constants";
import { FlowItem, FlowItemId, orderFlowItems } from "./flowLayout";
import { parseTimeToMinutes, toPayloadModule } from "./formatting";
import { cleanText, digitsOnly, firstError, intInRange } from "@/utils/validation";

export type EvaluationModuleState = Omit<ModuleConfig, "questionCount"> & {
  enabled: boolean;
  questionCount: string;
};

const emptyModule = (): EvaluationModuleState => ({
  enabled: false,
  checkIn: true,
  unlockCondition: "Automatic",
  questionCount: "",
});

export function useAddTrainingForm() {
  const router = useRouter();
  const { adminToken, admin, adminLogout } = useAuth();

  const [zone, setZone] = useState("");
  const [region, setRegion] = useState("");
  // The company this training belongs to is the logged-in admin/trainer's
  // own company (admin.company), not a user choice - see BasicDetailsSection,
  // which renders this locked rather than as an editable picker.
  const [company] = useState(admin?.company ?? "Samsung India");
  const [requestedByOption, setRequestedByOption] = useState("");
  const [requestedByOther, setRequestedByOther] = useState("");

  const [trainerId, setTrainerId] = useState("");
  const [trainerName, setTrainerName] = useState("");
  const [stateValue, setStateValue] = useState("");
  const [district, setDistrict] = useState("");
  const [venue, setVenue] = useState("");

  const [isResidential, setIsResidential] = useState(false);
  const [conferenceDate, setConferenceDate] = useState("");
  const [conferenceTime, setConferenceTime] = useState("");
  // Only shown/used when isResidential is on - a multi-day program's last day.
  const [trainingEndDate, setTrainingEndDate] = useState("");
  const [trainingHub, setTrainingHub] = useState("");
  const [audience, setAudience] = useState("");
  const [sessionType, setSessionType] = useState("");
  const [trainingType, setTrainingType] = useState("");
  const [batchSize, setBatchSize] = useState("");

  const [attendanceEnabled, setAttendanceEnabled] = useState(true);
  const [checkInOpens, setCheckInOpens] = useState("");
  const [checkOutCloses, setCheckOutCloses] = useState("");
  // Trainer only toggles geofencing on/off; the check-in radius is fixed at 100 m.
  const [geoFencing, setGeoFencing] = useState(true);

  const [modules, setModules] = useState<Record<ModuleKey, EvaluationModuleState>>({
    standardTest: emptyModule(),
    liveQuiz: emptyModule(),
    survey: emptyModule(),
  });
  // When each flow item was added, so the Session Flow cards can float the
  // newest (still un-timed) one to the top before it gets sorted by time.
  const [attendanceEnabledAt, setAttendanceEnabledAt] = useState(() => Date.now());
  const [moduleEnabledAt, setModuleEnabledAt] = useState<Partial<Record<ModuleKey, number>>>({});

  const [checklist, setChecklist] = useState<string[]>([]);
  const [agreeTerms, setAgreeTerms] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const [assessmentSuites, setAssessmentSuites] = useState<AssessmentSuiteOut[]>([]);
  const [trainerOptions, setTrainerOptions] = useState<SelectOption[]>([]);
  const [checklistOptions, setChecklistOptions] = useState<SelectOption[]>([]);
  const [venueOptions, setVenueOptions] = useState<SelectOption[]>([]);
  // Seeded with the static fallback list, replaced once the backend returns
  // real distinct values already used across past conferences - same
  // "learn from history" pattern as the trainer/venue/checklist pickers
  // above, just for fields that don't have a dedicated lookup table.
  // These pickers have no master table - their options are whatever values
  // this tenant has already used on past trainings (served by the /admin
  // catalog endpoints). Empty until the first fetch resolves.
  const [trainingHubOptions, setTrainingHubOptions] = useState<SelectOption[]>([]);
  const [audienceOptions, setAudienceOptions] = useState<SelectOption[]>([]);
  const [sessionTypeOptions, setSessionTypeOptions] = useState<SelectOption[]>([]);
  const [trainingTypeOptions, setTrainingTypeOptions] = useState<SelectOption[]>([]);
  const [requestedByOptions, setRequestedByOptions] = useState<SelectOption[]>([]);

  useEffect(() => {
    if (!adminToken) return;
    fetchAssessmentSuites(adminToken)
      .then(setAssessmentSuites)
      .catch(() => setAssessmentSuites([]));
    fetchTrainers(adminToken)
      .then(setTrainerOptions)
      .catch(() => setTrainerOptions([]));
    fetchChecklistItems(adminToken)
      .then(setChecklistOptions)
      .catch(() => setChecklistOptions([]));
    fetchTrainingHubs(adminToken)
      .then(setTrainingHubOptions)
      .catch(() => setTrainingHubOptions([]));
    fetchAudiences(adminToken)
      .then(setAudienceOptions)
      .catch(() => setAudienceOptions([]));
    fetchSessionTypes(adminToken)
      .then(setSessionTypeOptions)
      .catch(() => setSessionTypeOptions([]));
    fetchTrainingTypes(adminToken)
      .then(setTrainingTypeOptions)
      .catch(() => setTrainingTypeOptions([]));
    fetchRequestedByOptions(adminToken)
      .then(setRequestedByOptions)
      .catch(() => setRequestedByOptions([]));
  }, [adminToken]);

  // Venue is gated on District, so its options are re-fetched (scoped
  // server-side) each time the trainer picks a different district.
  useEffect(() => {
    const load = adminToken && district ? fetchVenues(adminToken, district) : Promise.resolve([]);
    load.then(setVenueOptions).catch(() => setVenueOptions([]));
  }, [adminToken, district]);

  const categoryOptions: SelectOption[] = useMemo(() => {
    const merged = new Map<string, SelectOption>();
    DEFAULT_CATEGORY_OPTIONS.forEach((option) => merged.set(option.value, option));
    assessmentSuites.forEach((suite) => merged.set(suite.category, { label: suite.category, value: suite.category }));
    return Array.from(merged.values());
  }, [assessmentSuites]);

  const questionSetOptionsFor = (category?: string): SelectOption[] => {
    const merged = new Map<string, SelectOption>();
    (DEFAULT_QUESTION_SET_OPTIONS[category ?? ""] ?? []).forEach((option) => merged.set(option.value, option));
    assessmentSuites
      .filter((suite) => suite.category === category)
      .forEach((suite) => merged.set(suite.assessmentSuiteUid, { label: suite.name, value: suite.assessmentSuiteUid }));
    return Array.from(merged.values());
  };

  const selectedState = useMemo(() => STATES.find((item) => item.value === stateValue), [stateValue]);

  const toggleResidential = (value: boolean) => {
    setIsResidential(value);
    if (!value) setTrainingEndDate("");
  };

  const toggleModule = (key: ModuleKey) => {
    const turningOn = !modules[key].enabled;
    setModules((prev) => ({ ...prev, [key]: { ...prev[key], enabled: !prev[key].enabled } }));
    setModuleEnabledAt((prev) => {
      const next = { ...prev };
      if (turningOn) next[key] = Date.now();
      else delete next[key];
      return next;
    });
  };

  const toggleAttendance = () => {
    if (!attendanceEnabled) setAttendanceEnabledAt(Date.now());
    setAttendanceEnabled((v) => !v);
  };

  const updateModule = (key: ModuleKey, patch: Partial<EvaluationModuleState>) => {
    setModules((prev) => ({ ...prev, [key]: { ...prev[key], ...patch } }));
  };

  const requestedBy = requestedByOption === "Other" ? requestedByOther : requestedByOption;

  const flowItemLabel = (id: FlowItemId): string =>
    id === "attendance" ? "Attendance" : MODULE_LABELS[id];

  const flowItemWindow = (id: FlowItemId): { start: string; end: string } =>
    id === "attendance"
      ? { start: checkInOpens, end: checkOutCloses }
      : { start: modules[id].startTime ?? "", end: modules[id].endTime ?? "" };

  // Attendance + every enabled module as one list, ordered by planned start
  // time (un-timed items float to the top, newest first). Drives both the
  // Session Flow cards and the backend's run order (via sessionConfig times).
  const orderedFlowItems = useMemo<FlowItem[]>(() => {
    const items: FlowItem[] = [];
    if (attendanceEnabled) {
      items.push({ id: "attendance", startTime: checkInOpens, enabledAt: attendanceEnabledAt });
    }
    (Object.keys(modules) as ModuleKey[]).forEach((key) => {
      if (modules[key].enabled) {
        items.push({ id: key, startTime: modules[key].startTime ?? "", enabledAt: moduleEnabledAt[key] ?? 0 });
      }
    });
    return orderFlowItems(items);
  }, [attendanceEnabled, checkInOpens, attendanceEnabledAt, modules, moduleEnabledAt]);

  // Modules run in start-time order now. Each needs a start + end, its end
  // must be after its start, and no two windows may overlap.
  const validateModuleSequence = (): string | null => {
    const windows = orderedFlowItems.map((item) => ({
      label: flowItemLabel(item.id),
      ...flowItemWindow(item.id),
    }));

    for (const w of windows) {
      if (!w.start || !w.end) return `${w.label} needs both a start and end time.`;
      const start = parseTimeToMinutes(w.start);
      const end = parseTimeToMinutes(w.end);
      if (start == null || end == null) return `${w.label} has an invalid time.`;
      if (end <= start) return `${w.label}'s end time must be after its start time.`;
    }

    for (let i = 1; i < windows.length; i++) {
      const previousEnd = parseTimeToMinutes(windows[i - 1].end)!;
      const currentStart = parseTimeToMinutes(windows[i].start)!;
      if (currentStart < previousEnd) {
        return `${windows[i].label} overlaps ${windows[i - 1].label} (which ends at ${windows[i - 1].end}).`;
      }
    }
    return null;
  };

  const handleSubmit = async () => {
    if (!conferenceDate || !conferenceTime) {
      setNotice("Training date and start time are required.");
      return;
    }
    if (isResidential && !trainingEndDate) {
      setNotice("End date is required for a residential program.");
      return;
    }
    if (isResidential && trainingEndDate < conferenceDate) {
      setNotice("End date can't be before the training date.");
      return;
    }
    if (!agreeTerms) {
      setNotice("Please agree to the Terms & Conditions to continue.");
      return;
    }
    if (!adminToken) {
      setNotice("Your session has expired. Please log in again.");
      return;
    }
    const sequenceError = validateModuleSequence();
    if (sequenceError) {
      setNotice(sequenceError);
      return;
    }

    const numberError = firstError(
      intInRange(batchSize, 1, 100000, "Batch size"),
      ...(["standardTest", "liveQuiz", "survey"] as ModuleKey[])
        .filter((key) => modules[key].enabled && modules[key].assessmentSuiteUid)
        .map((key) => {
          const suite = assessmentSuites.find(
            (item) => item.assessmentSuiteUid === modules[key].assessmentSuiteUid,
          );
          return intInRange(
            modules[key].questionCount,
            1,
            suite?.noOfQuestion ?? 999,
            `${MODULE_LABELS[key]} question count`,
            true,
          );
        }),
    );
    if (numberError) {
      setNotice(numberError);
      return;
    }

    setSubmitting(true);
    setNotice(null);
    try {
      await createTraining(adminToken, {
        zone: cleanText(zone, 100) || undefined,
        region: cleanText(region, 100) || undefined,
        company: cleanText(company, 120) || undefined,
        requestedBy: cleanText(requestedBy, 120) || undefined,
        trainerEmployeeId: trainerId || undefined,
        trainerName: trainerName || undefined,
        state: selectedState?.label,
        district: district || undefined,
        venue: venue || undefined,
        isResidential,
        conferenceDate,
        conferenceTime,
        trainingEndDate: isResidential ? trainingEndDate : undefined,
        trainingHub: trainingHub || undefined,
        audience: audience || undefined,
        sessionType: sessionType || undefined,
        trainingType: trainingType || undefined,
        batchSize: digitsOnly(batchSize) || undefined,
        sessionFlow: {
          attendance: attendanceEnabled
            ? {
                checkInOpens: checkInOpens || undefined,
                checkOutCloses: checkOutCloses || undefined,
                geoFencing,
                geoRadius: geoFencing ? 100 : undefined,
              }
            : undefined,
          standardTest: modules.standardTest.enabled ? toPayloadModule(modules.standardTest) : undefined,
          liveQuiz: modules.liveQuiz.enabled ? toPayloadModule(modules.liveQuiz) : undefined,
          survey: modules.survey.enabled ? toPayloadModule(modules.survey) : undefined,
        },
        checklist,
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
    company,
    requestedByOption, setRequestedByOption,
    requestedByOther, setRequestedByOther,
    requestedBy,
    requestedByOptions,

    trainerId, setTrainerId,
    trainerName, setTrainerName,
    trainerOptions,
    stateValue, setStateValue,
    district, setDistrict,
    venue, setVenue,
    venueOptions,
    selectedState,

    isResidential, setIsResidential, toggleResidential,
    conferenceDate, setConferenceDate,
    conferenceTime, setConferenceTime,
    trainingEndDate, setTrainingEndDate,
    trainingHub, setTrainingHub,
    trainingHubOptions,
    audience, setAudience,
    audienceOptions,
    sessionType, setSessionType,
    sessionTypeOptions,
    trainingType, setTrainingType,
    trainingTypeOptions,
    batchSize, setBatchSize,

    attendanceEnabled, setAttendanceEnabled, toggleAttendance,
    checkInOpens, setCheckInOpens,
    checkOutCloses, setCheckOutCloses,
    geoFencing, setGeoFencing,

    modules, toggleModule, updateModule,
    orderedFlowItems,
    categoryOptions, questionSetOptionsFor, assessmentSuites,
    checklistOptions,

    checklist, setChecklist,
    agreeTerms, setAgreeTerms,

    submitting, notice, handleSubmit,
  };
}

export type AddTrainingForm = ReturnType<typeof useAddTrainingForm>;
