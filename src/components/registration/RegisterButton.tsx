import React from "react";
import AppButton from "@/components/ui/AppButton";
import { Ionicons } from "@expo/vector-icons";

interface RegisterButtonProps {
  loading?: boolean;
  onPress: () => void;
}

export default function RegisterButton({
  loading = false,
  onPress,
}: RegisterButtonProps) {
  return (
    <AppButton
      title={loading ? "Registering..." : "Complete Registration"}
      onPress={onPress}
      loading={loading}
      rightIcon={
        <Ionicons
          name="arrow-forward"
          color="#fff"
        />
      }
    />
  );
}