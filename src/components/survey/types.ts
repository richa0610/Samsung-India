export type SurveyOption = {
  id: string;
  text: string;
};

export type SurveyQuestion = {
  id: string | number;
  question: string;
  type: "single-select" | "text";
  options?: SurveyOption[];
  required?: boolean;
};

export type SurveyAnswers = Record<string | number, string>;
