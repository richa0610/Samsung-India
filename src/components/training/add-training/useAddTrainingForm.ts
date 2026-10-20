import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "expo-router";

import { SelectOption } from "@/components/ui/SearchableSelect";
import { useAuth } from "@/hooks/useAuth";
import { useCompany } from "@/hooks/useCompany";
import { useStateDistricts } from "@/hooks/useStateDistricts";
import { subscribe } from "@/services/liveEvents";
import {
  ApiError,
  AssessmentSuiteOut,
  ApprovalStatus,
  MasterGroup,
  ModuleConfig,
  TrainingStatus,
  createTraining,
  fetchAssessmentSuites,
  fetchAudiences,
  fetchChecklistItems,
  fetchRequestedByOptions,
  fetchSessionTypes,
  fetchTrainers,
  fetchTrainingDetail,
  fetchTrainingHubs,
  fetchTrainingTypes,
  fetchVenues,
  fetchZones,
  updateTraining,
} from "@/api/training";
import { zoneKey } from "@/utils/zones";
import {
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

const toApprovalStatus = (value: string): ApprovalStatus =>
  value === "Approved" || value === "Rejected" ? value : "Pending";

// "Live" is the same running state as "Ongoing" for the admin's dropdown.
const toTrainingStatus = (value: string): TrainingStatus =>
  value === "Ongoing" || value === "Live"
    ? "Ongoing"
    : value === "Completed" || value === "Cancelled"
      ? value
      : "Scheduled";

// How often the review fields re-check the server while the page is open, as
// a backstop for a missed live push.
const LIVE_REFRESH_MS = 8000;

const asOptions = (names: string[]): SelectOption[] => names.map((name) => ({ label: name, value: name }));

// How a saved value is matched to the master list: names ignore case and spaces; a zone also
// ignores " Zone" ("North Zone" = "North"). State / District are matched by useStateDistricts.
const nameKey = (value: string) => value.trim().toLowerCase();

function findBy<T>(items: T[], value: string, key: (value: string) => string, nameOf: (item: T) => string): T | undefined {
  const wanted = key(value);
  return wanted ? items.find((item) => key(nameOf(item)) === wanted) : undefined;
}
const groupName = (group: MasterGroup) => group.name;
const itself = (name: string) => name;

// Passing an existing training's UID switches the form into edit mode: it
// loads that training's current detail into the same fields this hook
// already exposes (so the existing section components render unchanged),
// and submits via updateTraining instead of createTraining.
export function useAddTrainingForm(editing?: { conferenceUid: string }) {
  const router = useRouter();
  const { adminToken } = useAuth();
  const signedInCompany = useCompany()?.companyName ?? "";
  const isEditing = !!editing;

  const [loadingDetail, setLoadingDetail] = useState(isEditing);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [zone, setZone] = useState("");
  const [region, setRegion] = useState("");
  // A training's company is its tenant's - the server sets it, never the
  // form (user, 2026-10-18). Shown locked (BasicDetailsSection): the
  // signed-in company for a new training, the training's own for an edit.
  const [trainingCompany, setTrainingCompany] = useState<string | null>(null);
  const company = trainingCompany ?? signedInCompany;
  const [requestedByOption, setRequestedByOption] = useState("");
  const [requestedByOther, setRequestedByOther] = useState("");

  const [trainerId, setTrainerId] = useState("");
  const [trainerName, setTrainerName] = useState("");
  const [stateName, setStateName] = useState("");
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
  // Already agreed once at creation - editing an existing training shouldn't
  // re-prompt for Terms & Conditions.
  const [agreeTerms, setAgreeTerms] = useState(isEditing);

  // Admin review fields - only used in edit mode.
  const [attendanceSheetPax, setAttendanceSheetPax] = useState("");
  const [confirmedPax, setConfirmedPax] = useState("");
  const [approvalStatus, setApprovalStatus] = useState<ApprovalStatus>("Pending");
  const [originalApproval, setOriginalApproval] = useState<ApprovalStatus>("Pending");
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus>("Scheduled");
  const [adminMessage, setAdminMessage] = useState("");
  const [adminConfirm, setAdminConfirm] = useState(false);
  const [scheduleEditable, setScheduleEditable] = useState(true);
  const [evidence, setEvidence] = useState<{
    checkInPhoto?: string;
    checkOutPhoto?: string;
    attendanceSheet?: string;
  }>({});

  // Last value the server reported for each dropdown - a live refresh only
  // overwrites a dropdown the admin hasn't already changed themselves.
  const serverApprovalRef = useRef<ApprovalStatus>("Pending");
  const serverTrainingRef = useRef<TrainingStatus>("Scheduled");

  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  // Question sets per module - each list is fetched already filtered by the server.
  const [suitesByModule, setSuitesByModule] = useState<Record<ModuleKey, AssessmentSuiteOut[]>>({
    standardTest: [],
    liveQuiz: [],
    survey: [],
  });
  const assessmentSuites = useMemo(() => {
    const byUid = new Map<string, AssessmentSuiteOut>();
    Object.values(suitesByModule).flat().forEach((suite) => byUid.set(suite.assessmentSuiteUid, suite));
    return Array.from(byUid.values());
  }, [suitesByModule]);
  const [trainerOptions, setTrainerOptions] = useState<SelectOption[]>([]);
  const [checklistOptions, setChecklistOptions] = useState<SelectOption[]>([]);
  const [venueOptions, setVenueOptions] = useState<SelectOption[]>([]);
  // Zone / Region, Audience, Session Type and Training Type come from the master list (a
  // category's approved options - the zones each with their own regions); Training Hub and
  // Requested By, which have none, from the values this tenant already used on past trainings.
  // All served by the /admin catalog endpoints and empty until the first fetch resolves.
  // State / District come from the pincode directory (useStateDistricts, below).
  const [zoneGroups, setZoneGroups] = useState<MasterGroup[]>([]);
  const [trainingHubOptions, setTrainingHubOptions] = useState<SelectOption[]>([]);
  const [audienceOptions, setAudienceOptions] = useState<SelectOption[]>([]);
  const [sessionTypeOptions, setSessionTypeOptions] = useState<SelectOption[]>([]);
  const [trainingTypeOptions, setTrainingTypeOptions] = useState<SelectOption[]>([]);
  const [requestedByOptions, setRequestedByOptions] = useState<SelectOption[]>([]);

  useEffect(() => {
    if (!adminToken) return;
    (["standardTest", "liveQuiz", "survey"] as ModuleKey[]).forEach((key) => {
      fetchAssessmentSuites(adminToken, key)
        .then((suites) => setSuitesByModule((prev) => ({ ...prev, [key]: suites })))
        .catch(() => setSuitesByModule((prev) => ({ ...prev, [key]: [] })));
    });
    fetchTrainers(adminToken)
      .then(setTrainerOptions)
      .catch(() => setTrainerOptions([]));
    fetchZones(adminToken)
      .then(setZoneGroups)
      .catch(() => setZoneGroups([]));
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

  // Venue is gated on District (and its State - a district name two states share never mixes
  // their venues), so its options are re-fetched, scoped server-side, whenever either changes.
  useEffect(() => {
    const load = adminToken && district ? fetchVenues(adminToken, district, stateName) : Promise.resolve([]);
    load.then(setVenueOptions).catch(() => setVenueOptions([]));
  }, [adminToken, district, stateName]);

  // A value an older training saved ("North Zone", "new_delhi") is shown - and re-saved - as the
  // master spells it ("North", "New Delhi"); one the master doesn't have is kept as it is.
  const zoneGroup = findBy(zoneGroups, zone, zoneKey, groupName);
  const shownZone = zoneGroup?.name ?? zone;
  const shownRegion = findBy(zoneGroup?.options ?? [], region, nameKey, itself) ?? region;
  const zoneOptions = useMemo(() => asOptions(zoneGroups.map((group) => group.name)), [zoneGroups]);
  const regionOptions = useMemo(() => asOptions(zoneGroup?.options ?? []), [zoneGroup]);
  const { stateOptions, districtOptions, shownState, shownDistrict } = useStateDistricts(stateName, district);

  useEffect(() => {
    if (!editing || !adminToken) return;
    let cancelled = false;
    fetchTrainingDetail(adminToken, editing.conferenceUid)
      .then((detail) => {
        if (cancelled) return;
        setTrainingCompany(detail.company ?? null);
        setZone(detail.zone ?? "");
        setRegion(detail.region ?? "");
        // The stored value is already whatever the admin resolved it to last
        // time (a known option or a free-typed name) - "Other" + that text
        // always displays and resubmits it correctly either way.
        setRequestedByOption(detail.requestedBy ? "Other" : "");
        setRequestedByOther(detail.requestedBy ?? "");

        setTrainerId(detail.trainerEmployeeId ?? "");
        setTrainerName(detail.trainerName ?? "");
        setStateName(detail.state ?? "");
        setDistrict(detail.district ?? "");
        setVenue(detail.venue ?? "");

        setIsResidential(detail.isResidential);
        setConferenceDate(detail.conferenceDate ?? "");
        setConferenceTime(detail.conferenceTime ?? "");
        setTrainingEndDate(detail.trainingEndDate ?? "");
        setTrainingHub(detail.trainingHub ?? "");
        setAudience(detail.audience ?? "");
        setSessionType(detail.sessionType ?? "");
        setTrainingType(detail.trainingType ?? "");
        setBatchSize(detail.batchSize ?? "");

        const flow = detail.sessionFlow;
        if (flow?.attendance) {
          setAttendanceEnabled(true);
          setCheckInOpens(flow.attendance.checkInOpens ?? "");
          setCheckOutCloses(flow.attendance.checkOutCloses ?? "");
          setGeoFencing(flow.attendance.geoFencing);
        } else {
          setAttendanceEnabled(false);
        }

        const now = Date.now();
        const nextModules: Record<ModuleKey, EvaluationModuleState> = {
          standardTest: emptyModule(),
          liveQuiz: emptyModule(),
          survey: emptyModule(),
        };
        const nextEnabledAt: Partial<Record<ModuleKey, number>> = {};
        (["standardTest", "liveQuiz", "survey"] as ModuleKey[]).forEach((key) => {
          const module = flow?.[key];
          if (!module) return;
          nextModules[key] = {
            enabled: true,
            category: module.category,
            assessmentSuiteUid: module.assessmentSuiteUid,
            questionCount: module.questionCount != null ? String(module.questionCount) : "",
            startTime: module.startTime,
            endTime: module.endTime,
            checkIn: module.checkIn,
            unlockCondition: module.unlockCondition ?? "Automatic",
          };
          nextEnabledAt[key] = now;
        });
        setModules(nextModules);
        setModuleEnabledAt(nextEnabledAt);
        setAttendanceEnabledAt(now);

        setChecklist(detail.checklist ?? []);

        setAttendanceSheetPax(detail.attendanceSheetPax ?? "0");
        setConfirmedPax(detail.confirmedPax && detail.confirmedPax !== "0" ? detail.confirmedPax : "");
        const approval = toApprovalStatus(detail.approvalStatus);
        setApprovalStatus(approval);
        setOriginalApproval(approval);
        serverApprovalRef.current = approval;
        const training = toTrainingStatus(detail.conferenceStatus);
        setTrainingStatus(training);
        serverTrainingRef.current = training;
        setAdminMessage(detail.remarks ?? "");
        setScheduleEditable(detail.scheduleEditable);
        setEvidence({
          checkInPhoto: detail.checkInPhoto,
          checkOutPhoto: detail.checkOutPhoto,
          attendanceSheet: detail.attendanceSheet,
        });
      })
      .catch((err) => {
        if (cancelled) return;
        setLoadError(err instanceof ApiError ? err.message : "Couldn't load this training's details.");
      })
      .finally(() => {
        if (!cancelled) setLoadingDetail(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `editing` is a fresh object each render; its conferenceUid is the real trigger
  }, [editing?.conferenceUid, adminToken]);

  // Post-Training Data + Session Evidence are live: once the trainer starts
  // the session the status flips to Started, and their check-in / check-out
  // photos and attendance sheet appear as they're captured - no reopening.
  useEffect(() => {
    if (!editing || !adminToken) return;
    let cancelled = false;
    const refresh = () => {
      fetchTrainingDetail(adminToken, editing.conferenceUid)
        .then((detail) => {
          if (cancelled) return;
          setAttendanceSheetPax(detail.attendanceSheetPax ?? "0");
          setScheduleEditable(detail.scheduleEditable);
          setEvidence({
            checkInPhoto: detail.checkInPhoto,
            checkOutPhoto: detail.checkOutPhoto,
            attendanceSheet: detail.attendanceSheet,
          });

          const training = toTrainingStatus(detail.conferenceStatus);
          const previousTraining = serverTrainingRef.current;
          serverTrainingRef.current = training;
          setTrainingStatus((current) => (current === previousTraining ? training : current));

          const approval = toApprovalStatus(detail.approvalStatus);
          const previousApproval = serverApprovalRef.current;
          serverApprovalRef.current = approval;
          setOriginalApproval(approval);
          setApprovalStatus((current) => (current === previousApproval ? approval : current));
        })
        .catch(() => {});
    };
    const timer = setInterval(refresh, LIVE_REFRESH_MS);
    const unsubscribers = [
      subscribe("training_status_changed", refresh),
      subscribe("training_updated", refresh),
      subscribe("attendance_marked", refresh),
    ];
    return () => {
      cancelled = true;
      clearInterval(timer);
      unsubscribers.forEach((unsubscribe) => unsubscribe());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `editing` is a fresh object each render; its conferenceUid is the real trigger
  }, [editing?.conferenceUid, adminToken]);

  // Only real, approved question sets, already filtered per module by the server.
  const categoryOptionsFor = (key: ModuleKey): SelectOption[] => {
    const merged = new Map<string, SelectOption>();
    suitesByModule[key].forEach((suite) => merged.set(suite.category, { label: suite.category, value: suite.category }));
    return Array.from(merged.values());
  };

  const questionSetOptionsFor = (key: ModuleKey, category?: string): SelectOption[] =>
    suitesByModule[key]
      .filter((suite) => suite.category === category)
      .map((suite) => ({ label: suite.name, value: suite.assessmentSuiteUid }));

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
    if (isEditing) {
      const decided = approvalStatus !== originalApproval && approvalStatus !== "Pending";
      if (decided && !adminMessage.trim()) {
        setNotice(`Add a message explaining why you are marking this training ${approvalStatus.toLowerCase()}.`);
        return;
      }
      if (!adminConfirm) {
        setNotice("Please confirm the details above are correct.");
        return;
      }
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
      const payload = {
        zone: cleanText(shownZone, 100) || undefined,
        region: cleanText(shownRegion, 100) || undefined,
        requestedBy: cleanText(requestedBy, 120) || undefined,
        trainerEmployeeId: trainerId || undefined,
        trainerName: trainerName || undefined,
        state: shownState || undefined,
        district: shownDistrict || undefined,
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
        ...(isEditing
          ? {
              confirmedPax: digitsOnly(confirmedPax) || undefined,
              approvalStatus,
              trainingStatus,
              message: adminMessage.trim() || undefined,
            }
          : {}),
      };

      if (editing) {
        await updateTraining(adminToken, editing.conferenceUid, payload);
      } else {
        await createTraining(adminToken, payload);
      }

      router.back();
    } catch (err) {
      // The sign-in ended: api/client.ts has already signed out and opened the login screen.
      if (err instanceof ApiError && err.status === 401) return;
      setNotice(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return {
    isEditing,
    loadingDetail,
    loadError,

    zone: shownZone, setZone,
    zoneOptions,
    region: shownRegion, setRegion,
    regionOptions,
    company,
    requestedByOption, setRequestedByOption,
    requestedByOther, setRequestedByOther,
    requestedBy,
    requestedByOptions,

    trainerId, setTrainerId,
    trainerName, setTrainerName,
    trainerOptions,
    stateName: shownState, setStateName,
    stateOptions,
    district: shownDistrict, setDistrict,
    districtOptions,
    venue, setVenue,
    venueOptions,

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
    categoryOptionsFor, questionSetOptionsFor, assessmentSuites,
    checklistOptions,

    checklist, setChecklist,
    agreeTerms, setAgreeTerms,

    attendanceSheetPax,
    confirmedPax, setConfirmedPax,
    approvalStatus, setApprovalStatus,
    originalApproval,
    trainingStatus, setTrainingStatus,
    adminMessage, setAdminMessage,
    adminConfirm, setAdminConfirm,
    scheduleEditable,
    evidence,

    submitting, notice, handleSubmit,
  };
}

export type AddTrainingForm = ReturnType<typeof useAddTrainingForm>;
