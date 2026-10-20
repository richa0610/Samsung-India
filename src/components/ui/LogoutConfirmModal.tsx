import ConfirmModal from "@/components/ui/ConfirmModal";

type LogoutConfirmModalProps = {
  visible: boolean;
  onCancel: () => void;
  onConfirm: () => void;
};

// Shared "Log Out?" confirmation - trainer dashboard, trainer profile, and
// trainee profile all logout through this one component now, instead of
// three separate ConfirmModal call sites that had drifted out of sync with
// each other's wording (trainer_dashboard's had a typo: "want exit").
export default function LogoutConfirmModal({ visible, onCancel, onConfirm }: LogoutConfirmModalProps) {
  return (
    <ConfirmModal
      visible={visible}
      icon="log-out-outline"
      tone="danger"
      title="Log Out?"
      message="Are you sure you want to exit?"
      onCancel={onCancel}
      onConfirm={onConfirm}
    />
  );
}
