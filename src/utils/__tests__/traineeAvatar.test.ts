import { expect, test } from "@jest/globals";

import { initialsOf } from "@/utils/initials";
import { genderKey, traineeAvatar } from "@/utils/traineeAvatar";

const MALE = require("@/assets/images/user_img/default_male.png");
const FEMALE = require("@/assets/images/user_img/default_female.png");

test.each(["male", "Male", "MALE", " male ", "m", "M", " m "])("%j is male", (value) => {
  expect(genderKey(value)).toBe("male");
});

test.each(["female", "Female", "FEMALE", "female ", "f", "F", " F "])("%j is female", (value) => {
  expect(genderKey(value)).toBe("female");
});

test.each(["", "   ", null, undefined, "Other", "Woman", "mf", "ma"])("%j is no known gender", (value) => {
  expect(genderKey(value)).toBeNull();
});

test("a gender typed loosely still gets its picture", () => {
  expect(traineeAvatar({ gender: " F ", profilePhoto: null })).toBe(FEMALE);
  expect(traineeAvatar({ gender: "m", profilePhoto: "default.png" })).toBe(MALE);
});

test("no photo and no known gender gives no picture - the avatar shows initials instead", () => {
  expect(traineeAvatar({ gender: null, profilePhoto: null })).toBeNull();
  expect(traineeAvatar({ gender: "Other", profilePhoto: "avatar.png" })).toBeNull();
  expect(traineeAvatar(null)).toBeNull();
});

test("a real photo still wins over gender, sent with the trainee's token", () => {
  const source = traineeAvatar({ gender: "f", profilePhoto: "trainee_photos/TRN1.jpg" }, "tok") as {
    uri: string;
    headers: Record<string, string>;
  };
  expect(source.uri.endsWith("/media/trainee_photos/TRN1.jpg")).toBe(true);
  expect(source.headers).toEqual({ Authorization: "Bearer tok" });
});

test.each([
  ["Pooja Sharma", "PS"],
  ["  pooja   sharma ", "PS"],
  ["Anil", "A"],
  ["Pooja Kumari Sharma", "PK"],
  ["", ""],
  [null, ""],
  [undefined, ""],
])("initials of %j are %j", (name, initials) => {
  expect(initialsOf(name)).toBe(initials);
});
