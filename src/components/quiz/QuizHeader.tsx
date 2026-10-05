import React from "react";
import QuizLiveHeader from "./QuizLiveHeader";

export default function QuizHeader({ onReset }: { onReset: () => void }) {
  return (
    <QuizLiveHeader
      onSync={onReset}
      onRefresh={onReset}
      isConnected={true}
    />
  );
}

