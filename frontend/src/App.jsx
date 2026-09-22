import React, {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  Activity,
  AlertCircle,
  Archive,
  ArrowRight,
  BadgeCheck,
  Ban,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Clock3,
  Cloud,
  CloudOff,
  Database,
  FileCheck2,
  FileClock,
  FileSearch,
  FileText,
  Fingerprint,
  History,
  Globe2,
  Info,
  KeyRound,
  Layers3,
  LockKeyhole,
  Menu,
  Network,
  Play,
  RefreshCw,
  RotateCcw,
  Search,
  Send,
  Server,
  Shield,
  ShieldCheck,
  Sparkles,
  Upload,
  Wifi,
  WifiOff,
  X,
  XCircle,
  Zap,
} from "lucide-react";

/* =========================================================
   CONFIGURATION
========================================================= */

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

/* =========================================================
   HELPERS
========================================================= */

function pretty(value) {
  if (value === null || value === undefined) {
    return "—";
  }

  if (typeof value === "string") {
    return value;
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) {
    return "—";
  }

  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatTime(value) {
  if (!value) {
    return "—";
  }

  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function getValidationStatus(validation) {
  return (
    validation?.status ||
    validation?.verdict ||
    validation?.result ||
    "UNKNOWN"
  );
}

function isVerified(validation) {
  const status = getValidationStatus(validation);

  return (
    status === "VERIFIED" ||
    status === "VALID" ||
    status === "PASSED"
  );
}

function isFailed(validation) {
  const status = getValidationStatus(validation);

  return (
    status === "FAILED" ||
    status === "INVALID" ||
    status === "BLOCKED"
  );
}

async function apiRequest(
  endpoint,
  options = {}
) {
  const response = await fetch(
    `${API_BASE}${endpoint}`,
    options
  );

  const rawText = await response.text();

  let data = null;

  try {
    data = rawText ? JSON.parse(rawText) : null;
  } catch {
    data = rawText;
  }

  if (!response.ok) {
    const detail =
      typeof data === "object" && data?.detail
        ? data.detail
        : data;

    throw new Error(
      typeof detail === "string"
        ? detail
        : pretty(detail || `HTTP ${response.status}`)
    );
  }

  return data;
}

/* =========================================================
   SMALL UI COMPONENTS
========================================================= */

function StatusPill({
  status,
  children,
}) {
  const normalized = String(
    status || children || "UNKNOWN"
  ).toUpperCase();

  let styles =
    "border-slate-200 bg-slate-50 text-slate-600";

  if (
    normalized.includes("VERIFIED") ||
    normalized.includes("PASSED") ||
    normalized.includes("RECOVERED") ||
    normalized.includes("CONFIRMED")
  ) {
    styles =
      "border-emerald-200 bg-emerald-50 text-emerald-700";
  } else if (
    normalized.includes("FAILED") ||
    normalized.includes("BLOCKED") ||
    normalized.includes("CONFLICT") ||
    normalized.includes("FALSE")
  ) {
    styles =
      "border-red-200 bg-red-50 text-red-700";
  } else if (
    normalized.includes("PENDING") ||
    normalized.includes("REVIEW") ||
    normalized.includes("REQUIRED")
  ) {
    styles =
      "border-amber-200 bg-amber-50 text-amber-700";
  } else if (
    normalized.includes("PROCESS") ||
    normalized.includes("RUNNING") ||
    normalized.includes("ACTIVE")
  ) {
    styles =
      "border-blue-200 bg-blue-50 text-blue-700";
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide ${styles}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {children || normalized}
    </span>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  description,
  accent = "blue",
}) {
  const accentMap = {
    blue: "bg-blue-50 text-blue-700",
    green: "bg-emerald-50 text-emerald-700",
    amber: "bg-amber-50 text-amber-700",
    purple: "bg-violet-50 text-violet-700",
  };

  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
            {label}
          </p>

          <div className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
            {value}
          </div>

          {description && (
            <p className="mt-1 text-xs text-slate-500">
              {description}
            </p>
          )}
        </div>

        <div
          className={`rounded-xl p-2.5 ${accentMap[accent] || accentMap.blue}`}
        >
          <Icon size={19} />
        </div>
      </div>
    </div>
  );
}

function EmptyState({
  icon: Icon,
  title,
  description,
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/70 px-6 py-14 text-center">
      <div className="rounded-2xl bg-white p-3 shadow-sm">
        <Icon
          size={25}
          className="text-slate-400"
        />
      </div>

      <h3 className="mt-4 text-sm font-bold text-slate-800">
        {title}
      </h3>

      <p className="mt-1 max-w-md text-xs leading-5 text-slate-500">
        {description}
      </p>
    </div>
  );
}

/* =========================================================
   NAVIGATION
========================================================= */

const navigation = [
  {
    id: "overview",
    label: "Overview",
    icon: Activity,
  },
  {
    id: "verify",
    label: "Verify Document",
    icon: FileCheck2,
  },
  {
    id: "workflow",
    label: "Agent Workflow",
    icon: Network,
  },
  {
    id: "browser",
    label: "Website Automation",
    icon: Globe2,
  },
  {
    id: "evidence",
    label: "Evidence Vault",
    icon: ShieldCheck,
  },
  {
    id: "recovery",
    label: "Recovery",
    icon: RotateCcw,
  },
  {
    id: "offline",
    label: "Offline Mode",
    icon: WifiOff,
  },
];

/* =========================================================
   MAIN APP
========================================================= */

export default function App() {
  const [activePage, setActivePage] =
    useState("overview");

  const [sidebarOpen, setSidebarOpen] =
    useState(false);

  const [backendOnline, setBackendOnline] =
    useState(false);

  const [selectedFile, setSelectedFile] =
    useState(null);

  const [uploadResult, setUploadResult] =
    useState(null);

  const [validationResult, setValidationResult] =
    useState(null);

  const [uploading, setUploading] =
    useState(false);

  const [uploadError, setUploadError] =
    useState("");

  const [workflowId, setWorkflowId] =
    useState("");

  const [applicationId, setApplicationId] =
    useState("APP-DEMO-001");

  const [workflowData, setWorkflowData] =
    useState(null);

  const [workflowLoading, setWorkflowLoading] =
    useState(false);

  const [workflowError, setWorkflowError] =
    useState("");

  const [browserUrl, setBrowserUrl] =
    useState("https://form.jotform.com/262642652527056");

  const [browserName, setBrowserName] =
    useState("Test User");

  const [browserEmail, setBrowserEmail] =
    useState("");

  const [verifiedBrowserData, setVerifiedBrowserData] =
    useState(null);

  const [browserResult, setBrowserResult] =
    useState(null);

  const [browserLoading, setBrowserLoading] =
    useState(false);

  const [evidence, setEvidence] =
    useState([]);

  const [evidenceLoading, setEvidenceLoading] =
    useState(false);

  const [crossCheckData, setCrossCheckData] =
    useState({
      name: "Koushik V",
      dob: "",
      documentName: "",
      documentDob: "",
    });

  const [crossCheckResult, setCrossCheckResult] =
    useState(null);

  const [crossCheckLoading, setCrossCheckLoading] =
    useState(false);

  const [submissionId, setSubmissionId] =
    useState("");

  const [submissionResult, setSubmissionResult] =
    useState(null);

  const [submissionLoading, setSubmissionLoading] =
    useState(false);

  const [recoveryType, setRecoveryType] =
    useState("FILE_TOO_LARGE");

  const [recoveryResult, setRecoveryResult] =
    useState(null);

  const [recoveryLoading, setRecoveryLoading] =
    useState(false);

  const [offlineResult, setOfflineResult] =
    useState(null);

  const [offlineQueue, setOfflineQueue] =
    useState([]);

  const [offlineLoading, setOfflineLoading] =
    useState(false);

  const [toast, setToast] =
    useState(null);

  const fileInputRef = useRef(null);

  /* =====================================================
     TOAST
  ===================================================== */

  function showToast(
    message,
    type = "success"
  ) {
    setToast({
      message,
      type,
    });

    window.setTimeout(() => {
      setToast(null);
    }, 3500);
  }

  /* =====================================================
     BACKEND HEALTH
  ===================================================== */

  async function checkBackend() {
    try {
      const response = await fetch(
        `${API_BASE}/docs`
      );

      setBackendOnline(response.ok);
    } catch {
      setBackendOnline(false);
    }
  }

  useEffect(() => {
    checkBackend();

    const timer = window.setInterval(
      checkBackend,
      10000
    );

    return () =>
      window.clearInterval(timer);
  }, []);

  /* =====================================================
     FILE SELECTION
  ===================================================== */

  function handleFileSelected(event) {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);
    setUploadResult(null);
    setValidationResult(null);
    setUploadError("");

    showToast(
      `${file.name} selected`,
      "success"
    );
  }

  /* =====================================================
     REAL DOCUMENT UPLOAD
  ===================================================== */

  async function uploadDocument() {
    if (!selectedFile) {
      showToast(
        "Select a document first.",
        "error"
      );
      return;
    }

    setUploading(true);
    setUploadError("");
    setUploadResult(null);
    setValidationResult(null);

    try {
      const formData = new FormData();

      formData.append(
        "file",
        selectedFile
      );

      const data = await apiRequest(
        "/documents/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      setUploadResult(data);
      setValidationResult(
        data?.validation || null
      );

      showToast(
        "Document uploaded and validated.",
        "success"
      );

      await checkBackend();
    } catch (error) {
      setUploadError(
        error.message ||
          "Document upload failed."
      );

      showToast(
        "Document upload failed.",
        "error"
      );
    } finally {
      setUploading(false);
    }
  }

  /* =====================================================
     START AGENT WORKFLOW
  ===================================================== */

  async function startWorkflow() {
    setWorkflowLoading(true);
    setWorkflowError("");

    try {
      const body = {
        application_id:
          applicationId ||
          "APP-DEMO-001",
      };

      const data = await apiRequest(
        "/agent/start",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify(body),
        }
      );

      const id =
        data?.workflow_id ||
        data?.id ||
        "";

      setWorkflowId(id);
      setWorkflowData(data);

      showToast(
        id
          ? `Workflow ${id} started.`
          : "Workflow started.",
        "success"
      );
    } catch (error) {
      setWorkflowError(
        error.message ||
          "Could not start workflow."
      );

      showToast(
        "Could not start workflow.",
        "error"
      );
    } finally {
      setWorkflowLoading(false);
    }
  }

  /* =====================================================
     WORKFLOW STATUS
  ===================================================== */

  async function refreshWorkflow() {
    if (!workflowId) {
      showToast(
        "Start a workflow first.",
        "error"
      );
      return;
    }

    setWorkflowLoading(true);

    try {
      const data =
        await apiRequest(
          `/agent/status/${encodeURIComponent(
            workflowId
          )}`
        );

      setWorkflowData(data);

      showToast(
        "Workflow status refreshed.",
        "success"
      );
    } catch (error) {
      setWorkflowError(
        error.message ||
          "Could not retrieve workflow."
      );

      showToast(
        "Could not retrieve workflow.",
        "error"
      );
    } finally {
      setWorkflowLoading(false);
    }
  }

  /* =====================================================
     ADVANCE WORKFLOW
  ===================================================== */

  async function advanceWorkflow() {
    if (!workflowId) {
      showToast(
        "Start a workflow first.",
        "error"
      );
      return;
    }

    setWorkflowLoading(true);

    try {
      const data =
        await apiRequest(
          `/agent/advance/${encodeURIComponent(
            workflowId
          )}`,
          {
            method: "POST",
          }
        );

      setWorkflowData(data);

      showToast(
        "Workflow advanced.",
        "success"
      );
    } catch (error) {
      setWorkflowError(
        error.message ||
          "Workflow could not advance."
      );

      showToast(
        "Workflow advancement blocked.",
        "error"
      );
    } finally {
      setWorkflowLoading(false);
    }
  }

  /* =====================================================
     BLOCK WORKFLOW
  ===================================================== */

  async function blockWorkflow() {
    if (!workflowId) {
      showToast(
        "Start a workflow first.",
        "error"
      );
      return;
    }

    setWorkflowLoading(true);

    try {
      const data =
        await apiRequest(
          `/agent/block/${encodeURIComponent(
            workflowId
          )}`,
          {
            method: "POST",
          }
        );

      setWorkflowData(data);

      showToast(
        "Workflow blocked safely.",
        "success"
      );
    } catch (error) {
      setWorkflowError(
        error.message ||
          "Could not block workflow."
      );
    } finally {
      setWorkflowLoading(false);
    }
  }

  /* =====================================================
     RECOVER WORKFLOW
  ===================================================== */

  async function recoverWorkflow() {
    if (!workflowId) {
      showToast(
        "Start a workflow first.",
        "error"
      );
      return;
    }

    setWorkflowLoading(true);

    try {
      const data =
        await apiRequest(
          `/agent/recover/${encodeURIComponent(
            workflowId
          )}`,
          {
            method: "POST",
          }
        );

      setWorkflowData(data);

      showToast(
        "Recovery action executed.",
        "success"
      );
    } catch (error) {
      setWorkflowError(
        error.message ||
          "Recovery could not be executed."
      );

      showToast(
        "Recovery action failed.",
        "error"
      );
    } finally {
      setWorkflowLoading(false);
    }
  }

  /* =====================================================
     FINAL PROOF
  ===================================================== */

  async function createFinalProof() {
    if (!workflowId) {
      showToast(
        "Start a workflow first.",
        "error"
      );
      return;
    }

    setWorkflowLoading(true);

    try {
      const data =
        await apiRequest(
          `/agent/proof/${encodeURIComponent(
            workflowId
          )}`,
          {
            method: "POST",
          }
        );

      setWorkflowData(data);

      showToast(
        data?.status === "VERIFIED"
          ? "Final proof created."
          : "Final proof is still blocked.",
        data?.status === "VERIFIED"
          ? "success"
          : "error"
      );
    } catch (error) {
      setWorkflowError(
        error.message ||
          "Final proof could not be created."
      );

      showToast(
        "Final proof could not be created.",
        "error"
      );
    } finally {
      setWorkflowLoading(false);
    }
  }

  /* =====================================================
     WEBSITE BROWSER AUTOMATION
  ===================================================== */

  async function runBrowserApplication() {
    setBrowserLoading(true);
    setBrowserResult(null);
    setWorkflowError("");

    try {
      if (!uploadResult?.stored_path) {
        throw new Error(
          "Upload and verify a document first. Browser automation uses only verified document data."
        );
      }

      // Extract structured fields from the document already uploaded to DocuSure.
      // No name/email is typed manually into the browser workflow.
      const sourcePath =
        recoveryResult?.repaired_file ||
        uploadResult.stored_path;

      const verifiedData = await apiRequest(
        `/documents/verified-fields?file_path=${encodeURIComponent(sourcePath)}`
      );

      if (verifiedData?.status !== "VERIFIED") {
        throw new Error(
          verifiedData?.reason ||
            "Verified application fields could not be extracted from the document."
        );
      }

      const fieldValues = verifiedData?.fields || {};

      if (Object.keys(fieldValues).length === 0) {
        throw new Error(
          "No application fields were found in the verified document."
        );
      }

      setVerifiedBrowserData(verifiedData);
      setBrowserName(fieldValues["Full Name"] || "");
      setBrowserEmail(fieldValues["Email Address"] || fieldValues.Email || "");

      const startData = await apiRequest(
        "/agent/start",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            application_id:
              applicationId || "APP-BROWSER-001",
          }),
        }
      );

      const id =
        startData?.workflow_id ||
        startData?.id ||
        "";

      if (!id) {
        throw new Error(
          "Agent workflow did not return a workflow ID."
        );
      }

      setWorkflowId(id);
      setWorkflowData(startData);

      const browserData = await apiRequest(
        "/browser/application",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            url: browserUrl,
            field_values: fieldValues,
            submit: true,
          }),
        }
      );

      setBrowserResult(browserData);
      setWorkflowData(browserData);

      if (browserData?.status !== "VERIFIED") {
        showToast(
          "Website automation was blocked safely.",
          "error"
        );
        return;
      }

      const proofData = await apiRequest(
        `/agent/proof/${encodeURIComponent(id)}`,
        {
          method: "POST",
        }
      );

      setBrowserResult({
        ...browserData,
        final_proof: proofData,
      });

      setWorkflowData(proofData);

      if (proofData?.status === "VERIFIED") {
        showToast(
          "Verified document data submitted and final proof created.",
          "success"
        );
      } else {
        showToast(
          "Submission verified, but final proof is blocked.",
          "error"
        );
      }
    } catch (error) {
      const message =
        error?.message ||
        "Website automation failed.";

      setBrowserResult({
        status: "FAILED",
        reason: "BROWSER_WORKFLOW_ERROR",
        error: message,
      });

      setWorkflowError(message);

      showToast(
        message,
        "error"
      );
    } finally {
      setBrowserLoading(false);
    }
  }

  /* =====================================================
     EVIDENCE
  ===================================================== */

  async function loadEvidence() {
    setEvidenceLoading(true);

    try {
      const data =
        await apiRequest(
          "/verification/evidence"
        );

      const records = Array.isArray(data)
        ? data
        : data?.evidence ||
          data?.records ||
          [];

      setEvidence(records);

      showToast(
        `${records.length} evidence records loaded.`,
        "success"
      );
    } catch (error) {
      /*
        The backend EvidenceStore exists internally.
        If the current backend version does not expose
        this endpoint, keep the UI truthful rather than
        inventing records.
      */

      setEvidence([]);
      showToast(
        "Evidence endpoint is not exposed by the current backend.",
        "error"
      );
    } finally {
      setEvidenceLoading(false);
    }
  }

  /* =====================================================
     CROSS DOCUMENT CHECK
  ===================================================== */

  async function runCrossCheck() {
    setCrossCheckLoading(true);
    setCrossCheckResult(null);

    try {
      const payload = {
        name:
          crossCheckData.name || undefined,

        dob:
          crossCheckData.dob || undefined,

        document_name:
          crossCheckData.documentName ||
          undefined,

        document_dob:
          crossCheckData.documentDob ||
          undefined,
      };

      const data =
        await apiRequest(
          "/contracts/cross-check",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify(payload),
          }
        );

      setCrossCheckResult(data);

      showToast(
        data?.status === "BLOCKED"
          ? "Cross-document conflict detected."
          : "Cross-document verification completed.",
        data?.status === "BLOCKED"
          ? "error"
          : "success"
      );
    } catch (error) {
      setCrossCheckResult({
        status: "FAILED",
        error: error.message,
      });

      showToast(
        "Cross-document check failed.",
        "error"
      );
    } finally {
      setCrossCheckLoading(false);
    }
  }

  /* =====================================================
     SUBMISSION
  ===================================================== */

  async function submitApplication() {
    setSubmissionLoading(true);
    setSubmissionResult(null);

    try {
      const payload = {
        application_id:
          applicationId ||
          "APP-DEMO-001",
      };

      const data =
        await apiRequest(
          "/submission/submit",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify(payload),
          }
        );

      setSubmissionResult(data);

      if (data?.submission_id) {
        setSubmissionId(
          data.submission_id
        );
      }

      showToast(
        "Submission request completed.",
        "success"
      );
    } catch (error) {
      setSubmissionResult({
        status: "FAILED",
        error: error.message,
      });

      showToast(
        "Submission failed.",
        "error"
      );
    } finally {
      setSubmissionLoading(false);
    }
  }

  async function verifySubmission() {
    if (!submissionId) {
      showToast(
        "No submission ID available.",
        "error"
      );
      return;
    }

    setSubmissionLoading(true);

    try {
      const data =
        await apiRequest(
          "/submission/verify",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              submission_id:
                submissionId,
            }),
          }
        );

      setSubmissionResult(data);

      if (
        data?.verification ===
        "SUBMISSION_CONFIRMED"
      ) {
        showToast(
          "Submission independently verified.",
          "success"
        );
      } else {
        showToast(
          "Verification detected an unresolved state.",
          "error"
        );
      }
    } catch (error) {
      setSubmissionResult({
        status: "FAILED",
        error: error.message,
      });

      showToast(
        "Submission verification failed.",
        "error"
      );
    } finally {
      setSubmissionLoading(false);
    }
  }

  async function recoverSubmission() {
    if (!submissionId) {
      showToast(
        "No submission ID available.",
        "error"
      );
      return;
    }

    setSubmissionLoading(true);

    try {
      const data =
        await apiRequest(
          "/submission/recover",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              submission_id:
                submissionId,
            }),
          }
        );

      setSubmissionResult(data);

      showToast(
        "Submission recovery executed.",
        "success"
      );
    } catch (error) {
      setSubmissionResult({
        status: "FAILED",
        error: error.message,
      });

      showToast(
        "Submission recovery failed.",
        "error"
      );
    } finally {
      setSubmissionLoading(false);
    }
  }

  /* =====================================================
     DOCUMENT RECOVERY
  ===================================================== */

  async function recoverDocument() {
    if (!uploadResult?.document_id) {
      showToast(
        "Upload a document first.",
        "error"
      );
      return;
    }

    setRecoveryLoading(true);
    setRecoveryResult(null);

    try {
      const data =
        await apiRequest(
          `/documents/recover?document_id=${encodeURIComponent(
            uploadResult.document_id
          )}&failure_type=${encodeURIComponent(
            recoveryType
          )}`,
          {
            method: "POST",
          }
        );

      setRecoveryResult(data);

      showToast(
        "Document recovery completed.",
        "success"
      );
    } catch (error) {
      setRecoveryResult({
        status: "FAILED",
        error: error.message,
      });

      showToast(
        "Document recovery failed.",
        "error"
      );
    } finally {
      setRecoveryLoading(false);
    }
  }

  /* =====================================================
     OFFLINE
  ===================================================== */

  async function runOfflineValidation() {
    if (!uploadResult?.stored_path) {
      showToast(
        "Upload a document first.",
        "error"
      );
      return;
    }

    setOfflineLoading(true);
    setOfflineResult(null);

    try {
      const data =
        await apiRequest(
          "/offline/validate",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              application_id:
                applicationId ||
                "APP-DEMO-001",

              file_path:
                uploadResult.stored_path,
            }),
          }
        );

      setOfflineResult(data);

      showToast(
        "Offline validation completed and queued.",
        "success"
      );
    } catch (error) {
      setOfflineResult({
        status: "FAILED",
        error: error.message,
      });

      showToast(
        "Offline validation failed.",
        "error"
      );
    } finally {
      setOfflineLoading(false);
    }
  }

  async function loadOfflineQueue() {
    setOfflineLoading(true);

    try {
      const data =
        await apiRequest(
          "/offline/queue"
        );

      const queue =
        Array.isArray(data)
          ? data
          : data?.queue ||
            data?.events ||
            [];

      setOfflineQueue(queue);

      showToast(
        "Offline queue refreshed.",
        "success"
      );
    } catch (error) {
      setOfflineQueue([]);

      showToast(
        "Could not read offline queue.",
        "error"
      );
    } finally {
      setOfflineLoading(false);
    }
  }

  async function syncOfflineQueue() {
    setOfflineLoading(true);

    try {
      const data =
        await apiRequest(
          "/offline/sync",
          {
            method: "POST",
          }
        );

      setOfflineResult(data);

      await loadOfflineQueue();

      showToast(
        "Offline events synchronized.",
        "success"
      );
    } catch (error) {
      setOfflineResult({
        status: "FAILED",
        error: error.message,
      });

      showToast(
        "Offline synchronization failed.",
        "error"
      );
    } finally {
      setOfflineLoading(false);
    }
  }

  /* =====================================================
     DERIVED DATA
  ===================================================== */

  const currentValidationStatus =
    getValidationStatus(
      validationResult
    );

  const workflowStage =
    workflowData?.stage ||
    "NOT_STARTED";

  const workflowStatus =
    workflowData?.status ||
    "IDLE";

  const pendingOfflineCount =
    offlineQueue.filter(
      (item) => !item.synced
    ).length;

  const evidenceStats = useMemo(() => {
    return {
      total: evidence.length,

      verified: evidence.filter(
        (item) =>
          item?.verdict ===
          "VERIFIED"
      ).length,

      blocked: evidence.filter(
        (item) =>
          item?.verdict ===
          "BLOCKED"
      ).length,

      human: evidence.filter(
        (item) =>
          item?.verdict ===
          "HUMAN_REVIEW_REQUIRED"
      ).length,
    };
  }, [evidence]);

  /* =====================================================
     PAGE: OVERVIEW
  ===================================================== */

  function renderOverview() {
    return (
      <div className="animate-fade-in space-y-6">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600">
            Control Center
          </p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
            Evidence-gated document operations
          </h1>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            DocuSure executes document workflows,
            verifies every critical state using
            machine-checkable evidence, and stops
            safely when proof is missing or conflicting.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            icon={Server}
            label="Backend"
            value={
              backendOnline
                ? "ONLINE"
                : "OFFLINE"
            }
            description={
              backendOnline
                ? "FastAPI responding"
                : "API unavailable"
            }
            accent={
              backendOnline
                ? "green"
                : "amber"
            }
          />

          <MetricCard
            icon={ShieldCheck}
            label="Evidence"
            value={
              evidence.length
                ? evidence.length
                : "—"
            }
            description="Loaded verification records"
            accent="blue"
          />

          <MetricCard
            icon={Network}
            label="Workflow"
            value={
              workflowId
                ? workflowStatus
                : "READY"
            }
            description={
              workflowId
                ? workflowStage
                : "No active workflow"
            }
            accent="purple"
          />

          <MetricCard
            icon={WifiOff}
            label="Offline Queue"
            value={
              offlineQueue.length
                ? offlineQueue.length
                : "0"
            }
            description={`${pendingOfflineCount} pending synchronization`}
            accent="amber"
          />
        </div>

        <div className="grid gap-5 xl:grid-cols-[1.35fr_0.65fr]">
          <div className="glass-card overflow-hidden rounded-2xl">
            <div className="border-b border-slate-100 px-6 py-5">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="section-title">
                    Verification pipeline
                  </h2>

                  <p className="mt-1 muted">
                    Every stage produces evidence before
                    the workflow is allowed to continue.
                  </p>
                </div>

                <Shield
                  size={21}
                  className="text-blue-600"
                />
              </div>
            </div>

            <div className="p-6">
              <div className="grid gap-3 md:grid-cols-5">
                {[
                  [
                    "01",
                    "Detect",
                    "Document received",
                    Upload,
                  ],
                  [
                    "02",
                    "Validate",
                    "Machine-checkable validation",
                    FileCheck2,
                  ],
                  [
                    "03",
                    "Cross-check",
                    "Compare trusted values",
                    Layers3,
                  ],
                  [
                    "04",
                    "Submit",
                    "Execute external action",
                    Send,
                  ],
                  [
                    "05",
                    "Prove",
                    "Independent verification",
                    BadgeCheck,
                  ],
                ].map(
                  (item, index) => {
                    const [
                      number,
                      title,
                      description,
                      Icon,
                    ] = item;

                    return (
                      <div
                        key={title}
                        className="relative rounded-2xl border border-slate-200 bg-slate-50/70 p-4"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-black tracking-widest text-slate-400">
                            {number}
                          </span>

                          <Icon
                            size={17}
                            className="text-blue-600"
                          />
                        </div>

                        <h3 className="mt-4 text-sm font-bold text-slate-900">
                          {title}
                        </h3>

                        <p className="mt-1 text-[11px] leading-4 text-slate-500">
                          {description}
                        </p>

                        {index < 4 && (
                          <ChevronRight
                            size={14}
                            className="absolute -right-2 top-1/2 hidden -translate-y-1/2 bg-white text-slate-400 md:block"
                          />
                        )}
                      </div>
                    );
                  }
                )}
              </div>
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-slate-900 p-2.5 text-white">
                <Fingerprint size={20} />
              </div>

              <div>
                <h2 className="section-title">
                  Zero-trust state
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Completion is never assumed.
                </p>
              </div>
            </div>

            <div className="mt-6 space-y-4">
              {[
                [
                  "Evidence before advancement",
                  "Critical workflow transitions require verified evidence.",
                ],
                [
                  "Conflict detection",
                  "Conflicting document values stop the workflow.",
                ],
                [
                  "False-success detection",
                  "Portal success is not accepted without independent verification.",
                ],
                [
                  "Recovery",
                  "Recoverable failures trigger a controlled recovery path.",
                ],
              ].map(
                ([title, description]) => (
                  <div
                    key={title}
                    className="flex gap-3"
                  >
                    <div className="mt-0.5 rounded-full bg-emerald-50 p-1.5 text-emerald-600">
                      <Check size={13} />
                    </div>

                    <div>
                      <p className="text-xs font-bold text-slate-800">
                        {title}
                      </p>

                      <p className="mt-0.5 text-[11px] leading-4 text-slate-500">
                        {description}
                      </p>
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="section-title">
                Start with a real document
              </h2>

              <p className="mt-1 muted">
                Upload a document and DocuSure will
                send it directly to the FastAPI backend.
              </p>
            </div>

            <button
              className="primary-btn"
              onClick={() =>
                setActivePage("verify")
              }
            >
              <FileSearch size={17} />
              Open verification
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* =====================================================
     PAGE: VERIFY
  ===================================================== */

  function renderVerify() {
    return (
      <div className="animate-fade-in space-y-6">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600">
            Document Verification
          </p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
            Verify a document
          </h1>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            Upload a real document to the existing
            DocuSure validation engine. The result shown
            below comes from the backend response.
          </p>
        </div>

        <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-blue-50 p-2.5 text-blue-700">
                <Upload size={20} />
              </div>

              <div>
                <h2 className="section-title">
                  Document intake
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Backend endpoint:
                  {" "}
                  <code>
                    POST /documents/upload
                  </code>
                </p>
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,.json"
              className="hidden"
              onChange={
                handleFileSelected
              }
            />

            <button
              type="button"
              onClick={() =>
                fileInputRef.current?.click()
              }
              className="mt-6 flex min-h-[230px] w-full flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/60 px-6 text-center transition hover:border-blue-300 hover:bg-blue-50/30"
            >
              <div className="rounded-2xl bg-white p-4 shadow-sm">
                <FileText
                  size={29}
                  className="text-blue-600"
                />
              </div>

              <p className="mt-4 text-sm font-bold text-slate-800">
                {selectedFile
                  ? selectedFile.name
                  : "Choose a document"}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                {selectedFile
                  ? `${formatBytes(
                      selectedFile.size
                    )} selected`
                  : "PDF, DOCX, TXT or JSON"}
              </p>

              {selectedFile && (
                <span className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1.5 text-[11px] font-bold text-blue-700">
                  <Check size={13} />
                  Ready for upload
                </span>
              )}
            </button>

            <button
              className="primary-btn mt-4 w-full"
              onClick={uploadDocument}
              disabled={
                uploading ||
                !selectedFile
              }
            >
              {uploading ? (
                <>
                  <RefreshCw
                    size={16}
                    className="animate-spin"
                  />
                  Uploading & validating...
                </>
              ) : (
                <>
                  <ShieldCheck size={16} />
                  Upload & Validate
                </>
              )}
            </button>

            {uploadError && (
              <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-xs text-red-700">
                <div className="flex gap-2">
                  <AlertCircle
                    size={16}
                    className="shrink-0"
                  />
                  <pre className="whitespace-pre-wrap font-sans">
                    {uploadError}
                  </pre>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-5">
            <div className="glass-card rounded-2xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="section-title">
                    Validation result
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    Backend-derived verification state
                  </p>
                </div>

                {validationResult && (
                  <StatusPill
                    status={
                      currentValidationStatus
                    }
                  />
                )}
              </div>

              {!validationResult ? (
                <div className="mt-6">
                  <EmptyState
                    icon={FileCheck2}
                    title="No validation result yet"
                    description="Upload a document to populate this panel with the actual backend validation response."
                  />
                </div>
              ) : (
                <div className="mt-6 space-y-4">
                  <div
                    className={`rounded-2xl border p-5 ${
                      isVerified(
                        validationResult
                      )
                        ? "border-emerald-200 bg-emerald-50/60"
                        : isFailed(
                              validationResult
                            )
                          ? "border-red-200 bg-red-50/60"
                          : "border-amber-200 bg-amber-50/60"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {isVerified(
                        validationResult
                      ) ? (
                        <CheckCircle2
                          className="mt-0.5 text-emerald-600"
                          size={22}
                        />
                      ) : isFailed(
                          validationResult
                        ) ? (
                        <XCircle
                          className="mt-0.5 text-red-600"
                          size={22}
                        />
                      ) : (
                        <Clock3
                          className="mt-0.5 text-amber-600"
                          size={22}
                        />
                      )}

                      <div>
                        <p className="text-sm font-bold text-slate-900">
                          {currentValidationStatus}
                        </p>

                        <p className="mt-1 text-xs leading-5 text-slate-600">
                          This state was returned by the
                          document validation engine.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <InfoBox
                      label="Document ID"
                      value={
                        uploadResult?.document_id
                      }
                    />

                    <InfoBox
                      label="Filename"
                      value={
                        uploadResult?.filename
                      }
                    />

                    <InfoBox
                      label="Stored path"
                      value={
                        uploadResult?.stored_path
                      }
                    />

                    <InfoBox
                      label="File size"
                      value={
                        selectedFile
                          ? formatBytes(
                              selectedFile.size
                            )
                          : "—"
                      }
                    />
                  </div>

                  <details className="rounded-xl border border-slate-200 bg-slate-50">
                    <summary className="cursor-pointer px-4 py-3 text-xs font-bold text-slate-700">
                      View raw backend response
                    </summary>

                    <pre className="max-h-80 overflow-auto border-t border-slate-200 p-4 text-[11px] leading-5 text-slate-600">
                      {pretty(
                        uploadResult
                      )}
                    </pre>
                  </details>
                </div>
              )}
            </div>

            <div className="glass-card rounded-2xl p-6">
              <div className="flex items-center gap-3">
                <LockKeyhole
                  size={19}
                  className="text-slate-700"
                />

                <div>
                  <h2 className="section-title">
                    Verification principle
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    No frontend-generated verification is used.
                  </p>
                </div>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <MiniPrinciple
                  icon={Database}
                  title="Backend"
                  text="The FastAPI service performs validation."
                />

                <MiniPrinciple
                  icon={Shield}
                  title="Evidence"
                  text="Critical claims must be backed by evidence."
                />

                <MiniPrinciple
                  icon={Ban}
                  title="Stop"
                  text="Failures and conflicts are not silently accepted."
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* =====================================================
     PAGE: WORKFLOW
  ===================================================== */

  function renderWorkflow() {
    return (
      <div className="animate-fade-in space-y-6">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600">
            Agent Orchestration
          </p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
            Agent workflow
          </h1>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            Control the existing DocuSure orchestrator.
            The frontend does not decide whether a stage
            is verified — the backend evidence gates do.
          </p>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <div className="grid gap-4 lg:grid-cols-[1fr_1fr_auto]">
            <label>
              <span className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">
                Application ID
              </span>

              <input
                value={applicationId}
                onChange={(event) =>
                  setApplicationId(
                    event.target.value
                  )
                }
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-50"
                placeholder="APP-DEMO-001"
              />
            </label>

            <label>
              <span className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">
                Workflow ID
              </span>

              <input
                value={workflowId}
                onChange={(event) =>
                  setWorkflowId(
                    event.target.value
                  )
                }
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-50"
                placeholder="Generated after start"
              />
            </label>

            <div className="flex items-end">
              <button
                className="primary-btn w-full lg:w-auto"
                onClick={startWorkflow}
                disabled={workflowLoading}
              >
                <Play size={16} />
                Start
              </button>
            </div>
          </div>
        </div>

        <div className="grid gap-5 xl:grid-cols-[1fr_0.75fr]">
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="section-title">
                  Workflow state
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  {workflowId
                    ? workflowId
                    : "No workflow selected"}
                </p>
              </div>

              <StatusPill
                status={
                  workflowData?.status ||
                  "NOT_STARTED"
                }
              />
            </div>

            <div className="mt-6">
              <WorkflowRail
                currentStage={
                  workflowData?.stage
                }
                status={
                  workflowData?.status
                }
              />
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <button
                className="secondary-btn"
                onClick={refreshWorkflow}
                disabled={
                  workflowLoading ||
                  !workflowId
                }
              >
                <RefreshCw size={15} />
                Refresh
              </button>

              <button
                className="primary-btn"
                onClick={advanceWorkflow}
                disabled={
                  workflowLoading ||
                  !workflowId
                }
              >
                <ChevronRight size={15} />
                Advance
              </button>

              <button
                className="danger-btn"
                onClick={blockWorkflow}
                disabled={
                  workflowLoading ||
                  !workflowId
                }
              >
                <Ban size={15} />
                Block
              </button>

              <button
                className="secondary-btn"
                onClick={recoverWorkflow}
                disabled={
                  workflowLoading ||
                  !workflowId
                }
              >
                <RotateCcw size={15} />
                Recover
              </button>
            </div>

            <button
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700 transition hover:bg-emerald-100 disabled:opacity-50"
              onClick={createFinalProof}
              disabled={
                workflowLoading ||
                !workflowId
              }
            >
              <BadgeCheck size={17} />
              Create Final Proof
            </button>

            {workflowError && (
              <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-xs text-red-700">
                {workflowError}
              </div>
            )}
          </div>

          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3">
              <ShieldCheck
                size={19}
                className="text-emerald-600"
              />

              <div>
                <h2 className="section-title">
                  Current backend response
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Raw workflow state
                </p>
              </div>
            </div>

            <pre className="mt-5 max-h-[520px] overflow-auto rounded-xl bg-slate-950 p-4 text-[11px] leading-5 text-slate-300">
              {workflowData
                ? pretty(workflowData)
                : "No workflow response yet."}
            </pre>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-3">
            <Network
              size={19}
              className="text-blue-600"
            />

            <div>
              <h2 className="section-title">
                Evidence-gated progression
              </h2>

              <p className="mt-1 text-xs text-slate-500">
                Critical stages cannot simply be marked verified by the client.
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-5">
            {[
              "VALIDATION",
              "CROSS_CHECK",
              "APPROVAL",
              "SUBMISSION",
              "VERIFICATION",
            ].map((stage) => (
              <div
                key={stage}
                className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
              >
                <p className="text-[10px] font-black tracking-wider text-slate-400">
                  GATE
                </p>

                <p className="mt-1 text-xs font-bold text-slate-800">
                  {stage}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  /* =====================================================
     PAGE: WEBSITE AUTOMATION
  ===================================================== */

  function renderBrowser() {
    const resultEvidence =
      browserResult?.evidence || [];

    const finalProof =
      browserResult?.final_proof;

    return (
      <div className="animate-fade-in space-y-6">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600">
            Browser Agent
          </p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
            Website application automation
          </h1>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            DocuSure opens the target website, discovers its
            fields, fills verified data, reads the values back,
            submits the application, and requires independent
            submission evidence before creating final proof.
          </p>
        </div>

        <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-blue-50 p-2.5 text-blue-700">
                <Globe2 size={20} />
              </div>

              <div>
                <h2 className="section-title">
                  Application target
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Verified data is sent to the backend browser agent.
                </p>
              </div>
            </div>

            <div className="mt-6 space-y-4">
              <label className="block">
                <span className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Website URL
                </span>

                <input
                  value={browserUrl}
                  onChange={(event) =>
                    setBrowserUrl(event.target.value)
                  }
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-50 font-mono text-xs"
                />

                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => setBrowserUrl("https://form.jotform.com/262642652527056")}
                    className="rounded-lg border border-blue-200 bg-blue-50 px-2.5 py-1 text-[11px] font-semibold text-blue-700 hover:bg-blue-100"
                  >
                    Public Jotform Target
                  </button>
                  <button
                    type="button"
                    onClick={() => setBrowserUrl("http://127.0.0.1:8000/test-application")}
                    className="rounded-lg border border-slate-200 bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-200"
                  >
                    Local Test Application
                  </button>
                </div>
              </label>

              <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4">
                <p className="text-xs font-black uppercase tracking-wider text-blue-700">
                  Data source
                </p>
                <p className="mt-1 text-xs leading-5 text-blue-900">
                  Browser automation uses fields extracted from the uploaded and verified document. Nothing is manually invented for submission.
                </p>

                <div className="mt-3 space-y-2">
                  {verifiedBrowserData?.fields ? (
                    Object.entries(verifiedBrowserData.fields).map(
                      ([key, value]) => (
                        <div
                          key={key}
                          className="flex items-center justify-between gap-3 rounded-lg border border-blue-100 bg-white px-3 py-2"
                        >
                          <span className="text-xs font-semibold text-slate-500">
                            {key}
                          </span>
                          <span className="text-xs font-bold text-slate-900">
                            {String(value)}
                          </span>
                        </div>
                      )
                    )
                  ) : (
                    <p className="text-xs text-blue-800">
                      Upload a document and click Run Application Agent to load verified fields.
                    </p>
                  )}
                </div>
              </div>

              <button
                className="primary-btn w-full"
                onClick={runBrowserApplication}
                disabled={
                  browserLoading ||
                  !browserUrl ||
                  !uploadResult?.stored_path
                }
              >
                {browserLoading ? (
                  <>
                    <RefreshCw
                      size={16}
                      className="animate-spin"
                    />
                    Extracting verified data + running browser agent...
                  </>
                ) : (
                  <>
                    <Send size={16} />
                    Run From Verified Document
                  </>
                )}
              </button>
            </div>

            <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-bold text-slate-800">
                Safety rule
              </p>

              <p className="mt-1 text-[11px] leading-5 text-slate-500">
                If the agent cannot map fields, verify entered
                values, or independently confirm submission, the
                workflow is blocked instead of claiming success.
              </p>
            </div>
          </div>

          <div className="space-y-5">
            <div className="glass-card rounded-2xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="section-title">
                    Automation state
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    Live backend result
                  </p>
                </div>

                {browserResult && (
                  <StatusPill
                    status={browserResult.status}
                  />
                )}
              </div>

              {!browserResult ? (
                <div className="mt-5">
                  <EmptyState
                    icon={Globe2}
                    title="No browser run yet"
                    description="Start the agent to execute the real Playwright workflow."
                  />
                </div>
              ) : (
                <div className="mt-5 space-y-4">
                  <div className="grid gap-3 sm:grid-cols-3">
                    <InfoBox
                      label="Workflow"
                      value={workflowId}
                    />

                    <InfoBox
                      label="Result"
                      value={browserResult.reason}
                    />

                    <InfoBox
                      label="Final URL"
                      value={browserResult.final_url}
                    />
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                    <p className="text-xs font-black uppercase tracking-wider text-slate-400">
                      Verification chain
                    </p>

                    <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                      {[
                        ["Website Open", "WEBSITE_OPEN"],
                        ["Form Discovery", "FORM_DISCOVERY"],
                        ["Field Mapping", "FIELD_MAPPING"],
                        ["Form Filling", "FORM_FILLING"],
                        ["Read-back", "FORM_VALUE_VERIFICATION"],
                        ["Submission", "SUBMISSION_VERIFICATION"],
                      ].map(([label, type]) => {
                        const record =
                          resultEvidence.find(
                            (item) =>
                              item.evidence_type === type
                          );

                        const verified =
                          record?.verdict === "VERIFIED";

                        return (
                          <div
                            key={type}
                            className={`rounded-xl border p-3 ${
                              verified
                                ? "border-emerald-200 bg-emerald-50"
                                : record
                                  ? "border-red-200 bg-red-50"
                                  : "border-slate-200 bg-white"
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              {verified ? (
                                <CheckCircle2
                                  size={15}
                                  className="text-emerald-600"
                                />
                              ) : record ? (
                                <XCircle
                                  size={15}
                                  className="text-red-600"
                                />
                              ) : (
                                <CircleDot
                                  size={15}
                                  className="text-slate-400"
                                />
                              )}

                              <span className="text-[11px] font-bold text-slate-700">
                                {label}
                              </span>
                            </div>

                            <p className="mt-1 text-[9px] font-mono text-slate-400">
                              {record?.evidence_id || "PENDING"}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {finalProof?.status === "VERIFIED" && (
                    <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
                      <div className="flex items-center gap-3">
                        <div className="rounded-xl bg-white p-2 text-emerald-600 shadow-sm">
                          <BadgeCheck size={22} />
                        </div>

                        <div>
                          <p className="text-sm font-black text-emerald-800">
                            FINAL PROOF VERIFIED
                          </p>

                          <p className="mt-1 text-xs text-emerald-700">
                            Submission was independently confirmed
                            before proof was created.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  <details className="rounded-xl border border-slate-200 bg-slate-50">
                    <summary className="cursor-pointer px-4 py-3 text-xs font-bold text-slate-700">
                      View browser-agent response
                    </summary>

                    <pre className="max-h-96 overflow-auto border-t border-slate-200 p-4 text-[10px] leading-5 text-slate-600">
                      {pretty(browserResult)}
                    </pre>
                  </details>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* =====================================================
     PAGE: EVIDENCE
  ===================================================== */

  function renderEvidence() {
    return (
      <div className="animate-fade-in space-y-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600">
              Proof Layer
            </p>

            <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
              Evidence vault
            </h1>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
              Machine-checkable evidence is the basis for
              advancing critical workflow states.
            </p>
          </div>

          <button
            className="secondary-btn"
            onClick={loadEvidence}
            disabled={evidenceLoading}
          >
            <RefreshCw
              size={16}
              className={
                evidenceLoading
                  ? "animate-spin"
                  : ""
              }
            />
            Refresh Evidence
          </button>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            icon={Database}
            label="Records"
            value={evidenceStats.total}
            description="Loaded evidence records"
          />

          <MetricCard
            icon={CheckCircle2}
            label="Verified"
            value={evidenceStats.verified}
            description="Verified verdicts"
            accent="green"
          />

          <MetricCard
            icon={Ban}
            label="Blocked"
            value={evidenceStats.blocked}
            description="Blocked verdicts"
            accent="amber"
          />

          <MetricCard
            icon={AlertCircle}
            label="Human Review"
            value={evidenceStats.human}
            description="Manual review states"
            accent="purple"
          />
        </div>

        {evidence.length === 0 ? (
          <EmptyState
            icon={ShieldCheck}
            title="No evidence records loaded"
            description="Use Refresh Evidence if your backend exposes the evidence endpoint. The UI never fabricates evidence records."
          />
        ) : (
          <div className="space-y-3">
            {evidence.map(
              (record, index) => (
                <EvidenceCard
                  key={
                    record.evidence_id ||
                    index
                  }
                  record={record}
                />
              )
            )}
          </div>
        )}
      </div>
    );
  }

  /* =====================================================
     PAGE: RECOVERY
  ===================================================== */

  function renderRecovery() {
    return (
      <div className="animate-fade-in space-y-6">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600">
            Self-Healing Layer
          </p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
            Recovery center
          </h1>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            Recoverable failures are handled through
            explicit backend recovery policies rather
            than silently ignoring the failure.
          </p>
        </div>

        <div className="grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3">
              <RotateCcw
                size={20}
                className="text-blue-600"
              />

              <div>
                <h2 className="section-title">
                  Document recovery
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Uses the existing
                  {" "}
                  <code>
                    POST /documents/recover
                  </code>
                  {" "}
                  endpoint.
                </p>
              </div>
            </div>

            <div className="mt-6 space-y-4">
              <InfoBox
                label="Current document"
                value={
                  uploadResult?.document_id ||
                  "No document uploaded"
                }
              />

              <label>
                <span className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Failure type
                </span>

                <select
                  value={recoveryType}
                  onChange={(event) =>
                    setRecoveryType(
                      event.target.value
                    )
                  }
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-50"
                >
                  <option value="FILE_TOO_LARGE">
                    FILE_TOO_LARGE
                  </option>

                  <option value="INVALID_FILE_TYPE">
                    INVALID_FILE_TYPE
                  </option>

                  <option value="TEMPORARY_SERVER_ERROR">
                    TEMPORARY_SERVER_ERROR
                  </option>

                  <option value="FORM_VALUE_NOT_RETAINED">
                    FORM_VALUE_NOT_RETAINED
                  </option>

                  <option value="UNKNOWN_STATE">
                    UNKNOWN_STATE
                  </option>
                </select>
              </label>

              <button
                className="primary-btn w-full"
                onClick={recoverDocument}
                disabled={
                  recoveryLoading ||
                  !uploadResult?.document_id
                }
              >
                {recoveryLoading ? (
                  <>
                    <RefreshCw
                      size={16}
                      className="animate-spin"
                    />
                    Recovering...
                  </>
                ) : (
                  <>
                    <RotateCcw size={16} />
                    Run Recovery
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="section-title">
                  Recovery result
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Backend-generated recovery output
                </p>
              </div>

              {recoveryResult && (
                <StatusPill
                  status={
                    recoveryResult.status
                  }
                />
              )}
            </div>

            {!recoveryResult ? (
              <div className="mt-6">
                <EmptyState
                  icon={RotateCcw}
                  title="No recovery executed"
                  description="Upload a document and select a recoverable failure type to test the recovery engine."
                />
              </div>
            ) : (
              <pre className="mt-5 max-h-[480px] overflow-auto rounded-xl bg-slate-950 p-5 text-[11px] leading-5 text-slate-300">
                {pretty(
                  recoveryResult
                )}
              </pre>
            )}
          </div>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <h2 className="section-title">
            Recovery policy model
          </h2>

          <div className="mt-5 grid gap-3 md:grid-cols-3">
            <PolicyCard
              title="AUTO"
              description="Recoverable technical or document failures can be retried or transformed automatically."
              tone="green"
            />

            <PolicyCard
              title="HUMAN"
              description="Identity conflicts, OTP and CAPTCHA states require human intervention."
              tone="amber"
            />

            <PolicyCard
              title="STOP"
              description="Unknown states are blocked instead of being guessed through."
              tone="red"
            />
          </div>
        </div>
      </div>
    );
  }

  /* =====================================================
     PAGE: OFFLINE
  ===================================================== */

  function renderOffline() {
    return (
      <div className="animate-fade-in space-y-6">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600">
            Intermittent Connectivity
          </p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
            Offline continuity
          </h1>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            DocuSure can continue document validation
            locally during temporary connectivity loss,
            preserve the result in a persistent queue,
            and synchronize it after connectivity returns.
          </p>
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
          <OfflineStatusCard
            icon={
              backendOnline
                ? Wifi
                : WifiOff
            }
            title="Connectivity"
            value={
              backendOnline
                ? "CONNECTED"
                : "DISCONNECTED"
            }
            description={
              backendOnline
                ? "Backend is reachable."
                : "Backend is not currently reachable."
            }
            tone={
              backendOnline
                ? "green"
                : "amber"
            }
          />

          <OfflineStatusCard
            icon={FileCheck2}
            title="Critical function"
            value="LOCAL VALIDATION"
            description="Document validation runs through the local backend process."
            tone="blue"
          />

          <OfflineStatusCard
            icon={Archive}
            title="Queue"
            value={`${pendingOfflineCount} PENDING`}
            description="Events retained until synchronization."
            tone="purple"
          />
        </div>

        <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3">
              <CloudOff
                size={20}
                className="text-blue-600"
              />

              <div>
                <h2 className="section-title">
                  Offline validation
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Uses the existing backend offline endpoint.
                </p>
              </div>
            </div>

            <div className="mt-6 rounded-2xl border border-blue-100 bg-blue-50/60 p-5">
              <div className="flex gap-3">
                <Info
                  size={18}
                  className="mt-0.5 shrink-0 text-blue-600"
                />

                <div>
                  <p className="text-xs font-bold text-blue-900">
                    Demonstration flow
                  </p>

                  <p className="mt-1 text-xs leading-5 text-blue-800/80">
                    Upload a document, execute offline
                    validation, inspect the persistent
                    queue, then synchronize the queued
                    event.
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-5 space-y-3">
              <button
                className="primary-btn w-full"
                onClick={
                  runOfflineValidation
                }
                disabled={
                  offlineLoading ||
                  !uploadResult?.stored_path
                }
              >
                <FileCheck2 size={16} />
                Run Offline Validation
              </button>

              <button
                className="secondary-btn w-full"
                onClick={
                  loadOfflineQueue
                }
                disabled={
                  offlineLoading
                }
              >
                <Archive size={16} />
                Read Local Queue
              </button>

              <button
                className="secondary-btn w-full"
                onClick={
                  syncOfflineQueue
                }
                disabled={
                  offlineLoading
                }
              >
                <Cloud size={16} />
                Synchronize Queue
              </button>
            </div>

            {offlineResult && (
              <div className="mt-5">
                <p className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">
                  Latest response
                </p>

                <pre className="max-h-72 overflow-auto rounded-xl bg-slate-950 p-4 text-[11px] leading-5 text-slate-300">
                  {pretty(
                    offlineResult
                  )}
                </pre>
              </div>
            )}
          </div>

          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="section-title">
                  Persistent offline queue
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Events retained by the backend.
                </p>
              </div>

              <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-bold text-slate-600">
                {offlineQueue.length} events
              </span>
            </div>

            <div className="mt-5">
              {offlineQueue.length === 0 ? (
                <EmptyState
                  icon={Archive}
                  title="Queue is empty"
                  description="Run offline validation and refresh the queue to see persisted events."
                />
              ) : (
                <div className="space-y-3">
                  {offlineQueue.map(
                    (event) => (
                      <div
                        key={
                          event.event_id
                        }
                        className="rounded-xl border border-slate-200 bg-slate-50/70 p-4"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <p className="text-xs font-bold text-slate-900">
                              {
                                event.event_type
                              }
                            </p>

                            <p className="mt-1 font-mono text-[10px] text-slate-500">
                              {
                                event.event_id
                              }
                            </p>

                            <p className="mt-2 text-[11px] text-slate-500">
                              Application:
                              {" "}
                              {
                                event.application_id
                              }
                            </p>
                          </div>

                          <StatusPill
                            status={
                              event.synced
                                ? "SYNCED"
                                : "PENDING"
                            }
                          />
                        </div>

                        <div className="mt-3 border-t border-slate-200 pt-3">
                          <p className="text-[10px] text-slate-400">
                            Created
                          </p>

                          <p className="mt-0.5 text-[11px] text-slate-600">
                            {formatTime(
                              event.created_at
                            )}
                          </p>
                        </div>
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* =====================================================
     RENDER CURRENT PAGE
  ===================================================== */

  function renderPage() {
    switch (activePage) {
      case "verify":
        return renderVerify();

      case "workflow":
        return renderWorkflow();

      case "browser":
        return renderBrowser();

      case "evidence":
        return renderEvidence();

      case "recovery":
        return renderRecovery();

      case "offline":
        return renderOffline();

      case "overview":
      default:
        return renderOverview();
    }
  }

  /* =====================================================
     APP SHELL
  ===================================================== */

  return (
    <div className="min-h-screen bg-[#f7f9fc] text-slate-900">
      {/* MOBILE OVERLAY */}

      {sidebarOpen && (
        <button
          aria-label="Close menu"
          className="fixed inset-0 z-40 bg-slate-950/30 backdrop-blur-sm lg:hidden"
          onClick={() =>
            setSidebarOpen(false)
          }
        />
      )}

      {/* SIDEBAR */}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-[268px] flex-col border-r border-slate-200 bg-white transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen
            ? "translate-x-0"
            : "-translate-x-full"
        }`}
      >
        <div className="flex h-[74px] items-center justify-between border-b border-slate-100 px-5">
          <button
            className="flex items-center gap-3"
            onClick={() =>
              setActivePage("overview")
            }
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white shadow-sm">
              <ShieldCheck size={22} />
            </div>

            <div className="text-left">
              <div className="text-[17px] font-black tracking-tight text-slate-950">
                DocuSure
              </div>

              <div className="text-[9px] font-bold uppercase tracking-[0.18em] text-slate-400">
                Proof before completion
              </div>
            </div>
          </button>

          <button
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 lg:hidden"
            onClick={() =>
              setSidebarOpen(false)
            }
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-4 pt-6">
          <div className="mb-2 px-2 text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
            Workspace
          </div>

          <nav className="space-y-1">
            {navigation.map(
              ({
                id,
                label,
                icon: Icon,
              }) => {
                const active =
                  activePage === id;

                return (
                  <button
                    key={id}
                    onClick={() => {
                      setActivePage(id);
                      setSidebarOpen(false);
                    }}
                    className={`group flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition ${
                      active
                        ? "bg-slate-950 text-white shadow-sm"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    }`}
                  >
                    <Icon
                      size={18}
                      className={
                        active
                          ? "text-white"
                          : "text-slate-400 group-hover:text-slate-700"
                      }
                    />

                    <span className="text-sm font-semibold">
                      {label}
                    </span>

                    {id ===
                      "offline" &&
                      pendingOfflineCount >
                        0 && (
                        <span
                          className={`ml-auto rounded-full px-2 py-0.5 text-[9px] font-black ${
                            active
                              ? "bg-white/15 text-white"
                              : "bg-amber-100 text-amber-700"
                          }`}
                        >
                          {
                            pendingOfflineCount
                          }
                        </span>
                      )}
                  </button>
                );
              }
            )}
          </nav>
        </div>

        <div className="mt-auto p-4">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  backendOnline
                    ? "bg-emerald-500"
                    : "bg-amber-500"
                }`}
              />

              <span className="text-xs font-bold text-slate-700">
                API
              </span>

              <span className="ml-auto text-[10px] font-bold text-slate-400">
                :8000
              </span>
            </div>

            <p className="mt-2 text-[10px] leading-4 text-slate-500">
              {backendOnline
                ? "FastAPI backend is reachable."
                : "Backend connection unavailable."}
            </p>

            <button
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[10px] font-bold text-slate-600 hover:bg-slate-100"
              onClick={checkBackend}
            >
              <RefreshCw size={12} />
              Check connection
            </button>
          </div>
        </div>
      </aside>

      {/* MAIN */}

      <div className="lg:pl-[268px]">
        {/* TOP BAR */}

        <header className="sticky top-0 z-30 flex h-[74px] items-center justify-between border-b border-slate-200/80 bg-white/90 px-4 backdrop-blur md:px-7">
          <div className="flex items-center gap-3">
            <button
              className="rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 lg:hidden"
              onClick={() =>
                setSidebarOpen(true)
              }
            >
              <Menu size={19} />
            </button>

            <div className="hidden items-center gap-2 text-xs text-slate-400 sm:flex">
              <span>
                DocuSure
              </span>

              <ChevronRight
                size={13}
              />

              <span className="font-semibold text-slate-700">
                {
                  navigation.find(
                    (item) =>
                      item.id ===
                      activePage
                  )?.label
                }
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div
              className={`hidden items-center gap-2 rounded-full border px-3 py-1.5 text-[10px] font-bold sm:flex ${
                backendOnline
                  ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                  : "border-amber-200 bg-amber-50 text-amber-700"
              }`}
            >
              {backendOnline ? (
                <Wifi size={12} />
              ) : (
                <WifiOff size={12} />
              )}

              {backendOnline
                ? "BACKEND ONLINE"
                : "BACKEND OFFLINE"}
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-2.5 text-slate-500">
              <LockKeyhole size={17} />
            </div>
          </div>
        </header>

        {/* PAGE CONTENT */}

        <main className="mx-auto max-w-[1500px] px-4 py-7 md:px-7 lg:px-9">
          {renderPage()}
        </main>
      </div>

      {/* TOAST */}

      {toast && (
        <div className="fixed bottom-5 right-5 z-[100] max-w-sm animate-slide-up">
          <div
            className={`flex items-start gap-3 rounded-2xl border bg-white px-4 py-3 shadow-soft ${
              toast.type ===
              "error"
                ? "border-red-200"
                : "border-slate-200"
            }`}
          >
            {toast.type ===
            "error" ? (
              <AlertCircle
                size={18}
                className="mt-0.5 text-red-600"
              />
            ) : (
              <CheckCircle2
                size={18}
                className="mt-0.5 text-emerald-600"
              />
            )}

            <p className="text-xs font-semibold leading-5 text-slate-700">
              {toast.message}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

/* =========================================================
   SUPPORTING COMPONENTS
========================================================= */

function InfoBox({
  label,
  value,
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
      <p className="text-[9px] font-black uppercase tracking-[0.12em] text-slate-400">
        {label}
      </p>

      <p className="mt-1 break-all text-xs font-semibold text-slate-700">
        {value || "—"}
      </p>
    </div>
  );
}

function MiniPrinciple({
  icon: Icon,
  title,
  text,
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <Icon
        size={17}
        className="text-slate-600"
      />

      <p className="mt-3 text-xs font-bold text-slate-800">
        {title}
      </p>

      <p className="mt-1 text-[10px] leading-4 text-slate-500">
        {text}
      </p>
    </div>
  );
}

function WorkflowRail({
  currentStage,
  status,
}) {
  const stages = [
    "REQUIREMENTS",
    "DOCUMENTS",
    "VALIDATION",
    "CROSS_CHECK",
    "FORM_FILLING",
    "APPROVAL",
    "SUBMISSION",
    "VERIFICATION",
    "RECOVERY",
    "PROOF",
  ];

  const currentIndex =
    stages.indexOf(
      currentStage
    );

  return (
    <div className="space-y-2">
      {stages.map(
        (stage, index) => {
          const completed =
            currentIndex >= 0 &&
            index < currentIndex;

          const active =
            currentStage === stage;

          const blocked =
            status === "BLOCKED" &&
            active;

          return (
            <div
              key={stage}
              className={`flex items-center gap-3 rounded-xl border px-4 py-3 transition ${
                active
                  ? blocked
                    ? "border-red-200 bg-red-50"
                    : "border-blue-200 bg-blue-50"
                  : completed
                    ? "border-emerald-100 bg-emerald-50/60"
                    : "border-slate-100 bg-slate-50/60"
              }`}
            >
              <div
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-black ${
                  active
                    ? blocked
                      ? "bg-red-600 text-white"
                      : "bg-blue-600 text-white"
                    : completed
                      ? "bg-emerald-600 text-white"
                      : "bg-white text-slate-400"
                }`}
              >
                {completed ? (
                  <Check size={13} />
                ) : (
                  index + 1
                )}
              </div>

              <div className="min-w-0">
                <p
                  className={`text-xs font-bold ${
                    active
                      ? blocked
                        ? "text-red-800"
                        : "text-blue-800"
                      : completed
                        ? "text-emerald-800"
                        : "text-slate-600"
                  }`}
                >
                  {stage}
                </p>

                {active && (
                  <p className="mt-0.5 text-[10px] text-slate-500">
                    Current orchestrator stage
                  </p>
                )}
              </div>

              {active && (
                <span className="ml-auto">
                  <CircleDot
                    size={15}
                    className={
                      blocked
                        ? "text-red-500"
                        : "animate-pulse text-blue-500"
                    }
                  />
                </span>
              )}
            </div>
          );
        }
      )}
    </div>
  );
}

function EvidenceCard({
  record,
}) {
  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-[10px] font-bold text-slate-400">
              {record.evidence_id ||
                "NO-ID"}
            </span>

            <StatusPill
              status={
                record.verdict
              }
            />

            {record.evidence_type && (
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold text-slate-600">
                {
                  record.evidence_type
                }
              </span>
            )}
          </div>

          <h3 className="mt-3 text-sm font-bold text-slate-900">
            {record.claim ||
              "Evidence record"}
          </h3>

          <p className="mt-1 text-xs text-slate-500">
            Source:
            {" "}
            {record.source ||
              "Unknown"}
          </p>
        </div>

        <span className="shrink-0 text-[10px] text-slate-400">
          {formatTime(
            record.timestamp
          )}
        </span>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-[9px] font-black uppercase tracking-wider text-slate-400">
            Value
          </p>

          <pre className="mt-2 max-h-44 overflow-auto whitespace-pre-wrap break-words text-[10px] leading-5 text-slate-600">
            {pretty(
              record.value
            )}
          </pre>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-[9px] font-black uppercase tracking-wider text-slate-400">
            Metadata
          </p>

          <pre className="mt-2 max-h-44 overflow-auto whitespace-pre-wrap break-words text-[10px] leading-5 text-slate-600">
            {pretty(
              record.metadata
            )}
          </pre>
        </div>
      </div>
    </div>
  );
}

function PolicyCard({
  title,
  description,
  tone,
}) {
  const classes = {
    green:
      "border-emerald-200 bg-emerald-50 text-emerald-800",
    amber:
      "border-amber-200 bg-amber-50 text-amber-800",
    red:
      "border-red-200 bg-red-50 text-red-800",
  };

  return (
    <div
      className={`rounded-xl border p-4 ${
        classes[tone]
      }`}
    >
      <p className="text-xs font-black">
        {title}
      </p>

      <p className="mt-1 text-[11px] leading-5 opacity-80">
        {description}
      </p>
    </div>
  );
}

function OfflineStatusCard({
  icon: Icon,
  title,
  value,
  description,
  tone,
}) {
  const styles = {
    green:
      "bg-emerald-50 text-emerald-700",
    blue:
      "bg-blue-50 text-blue-700",
    amber:
      "bg-amber-50 text-amber-700",
    purple:
      "bg-violet-50 text-violet-700",
  };

  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.13em] text-slate-400">
            {title}
          </p>

          <p className="mt-2 text-lg font-black tracking-tight text-slate-900">
            {value}
          </p>

          <p className="mt-1 text-[11px] leading-4 text-slate-500">
            {description}
          </p>
        </div>

        <div
          className={`rounded-xl p-2.5 ${
            styles[tone] ||
            styles.blue
          }`}
        >
          <Icon size={19} />
        </div>
      </div>
    </div>
  );
}