import { Stack } from "expo-router";

export function AppStack() {
  return (
    <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: "transparent" } }}>
      <Stack.Screen name="index" />
      <Stack.Screen name="trainer_login" />
      <Stack.Screen name="trainer_dashboard" />
      <Stack.Screen name="trainer_profile" />
      <Stack.Screen name="admin_dashboard" />
      <Stack.Screen name="assessment_builder" />
      <Stack.Screen name="add_training" />
      <Stack.Screen name="pending_trainings" />
      <Stack.Screen name="training_list" />
      <Stack.Screen name="new_trainee" />
      <Stack.Screen name="pending_trainee" />
      <Stack.Screen name="sessions" />
      <Stack.Screen name="session_dashboard" />
      <Stack.Screen name="session_report" />
      <Stack.Screen name="session" />
      <Stack.Screen name="session_detail" />
      <Stack.Screen name="secure_checkin" />
      <Stack.Screen name="attendance" />
      <Stack.Screen name="attendance_list" />
      <Stack.Screen name="pending_attendance" />
      <Stack.Screen name="confirmed_attendance" />
      <Stack.Screen name="live_quiz" />
      <Stack.Screen name="quiz_leaderboard" />
      <Stack.Screen name="post_test" />
      <Stack.Screen name="survey" />
      <Stack.Screen name="profile" />
      <Stack.Screen name="participant_login" />
      <Stack.Screen name="scan" />
      <Stack.Screen name="join/[code]" />
      <Stack.Screen name="trainee_dashboard" />
      <Stack.Screen name="training_history" />
    </Stack>
  );
}
