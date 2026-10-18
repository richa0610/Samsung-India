import { beforeAll, beforeEach, expect, jest, test } from "@jest/globals";
import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";
import { Text } from "react-native";

import { ApiError } from "@/api/client";
import { lookupCompany } from "@/api/tenants";
import CompanyGate from "@/components/company/CompanyGate";
import { Company, setCompany } from "@/config/company";
import { COMPANY_TEXT } from "@/constants/strings";

let mockCompany: Company | null = null;

jest.mock("@/hooks/useCompany", () => ({ useCompany: () => mockCompany }));
jest.mock("@/api/tenants", () => ({ lookupCompany: jest.fn() }));
jest.mock("@/config/company", () => ({ setCompany: jest.fn(), getCompany: () => null }));

const mockLookup = jest.mocked(lookupCompany);
const mockSetCompany = jest.mocked(setCompany);
const ACME: Company = { tenantId: "acme", companyName: "Acme Retail" };

const gate = () =>
  render(
    <CompanyGate>
      <Text>sign-in options</Text>
    </CompanyGate>,
  );

// The first render loads the icon set from scratch; do it once here.
beforeAll(async () => {
  const first = await gate();
  await first.unmount();
}, 30_000);

beforeEach(() => {
  mockCompany = null;
  mockLookup.mockReset();
  mockSetCompany.mockReset();
});

test("without a company, only the company code form shows - no way around it", async () => {
  await gate();
  expect(screen.getByText(COMPANY_TEXT.title)).toBeTruthy();
  expect(screen.queryByText("sign-in options")).toBeNull();
  expect(screen.queryByText(COMPANY_TEXT.cancel)).toBeNull();
});

test("an empty code is refused without asking the server", async () => {
  await gate();
  await fireEvent.press(screen.getByText(COMPANY_TEXT.submit));
  expect(screen.getByText(COMPANY_TEXT.required)).toBeTruthy();
  expect(mockLookup).not.toHaveBeenCalled();
});

test("a code the server confirms becomes the device's company", async () => {
  mockLookup.mockResolvedValue(ACME);
  await gate();
  await fireEvent.changeText(screen.getByPlaceholderText(COMPANY_TEXT.placeholder), "  ACME ");
  await fireEvent.press(screen.getByText(COMPANY_TEXT.submit));
  await waitFor(() => expect(mockSetCompany).toHaveBeenCalledWith(ACME));
  expect(mockLookup).toHaveBeenCalledWith("ACME");
});

test("an unknown code shows the server's answer and saves nothing", async () => {
  mockLookup.mockRejectedValue(new ApiError("Company code not found", 404));
  await gate();
  await fireEvent.changeText(screen.getByPlaceholderText(COMPANY_TEXT.placeholder), "nope");
  await fireEvent.press(screen.getByText(COMPANY_TEXT.submit));
  expect(await screen.findByText("Company code not found")).toBeTruthy();
  expect(mockSetCompany).not.toHaveBeenCalled();
});

test("with a company: its name shows above the options, and Change can be cancelled", async () => {
  mockCompany = ACME;
  await gate();
  expect(screen.getByText("Acme Retail")).toBeTruthy();
  expect(screen.getByText("sign-in options")).toBeTruthy();

  await fireEvent.press(screen.getByLabelText(`${COMPANY_TEXT.change} ${COMPANY_TEXT.current.toLowerCase()}`));
  expect(screen.getByText(COMPANY_TEXT.title)).toBeTruthy();
  expect(screen.queryByText("sign-in options")).toBeNull();

  await fireEvent.press(screen.getByText(COMPANY_TEXT.cancel));
  expect(screen.getByText("sign-in options")).toBeTruthy();
});
