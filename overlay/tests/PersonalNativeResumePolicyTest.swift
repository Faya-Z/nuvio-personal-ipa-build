import Foundation
var checks = 0
func expect(_ condition: @autoclosure () -> Bool, _ label: String) {
    precondition(condition(), label)
    checks += 1
}
expect(PersonalNativeResumePolicy.startOption(positionMs: -1) == nil, "negative")
expect(PersonalNativeResumePolicy.startOption(positionMs: 0) == nil, "zero")
expect(PersonalNativeResumePolicy.startOption(positionMs: 999) == nil, "tiny")
expect(PersonalNativeResumePolicy.startOption(positionMs: 1_000) == "start=1.000", "minimum")
expect(PersonalNativeResumePolicy.startOption(positionMs: 1_001) == "start=1.001", "millisecond")
expect(PersonalNativeResumePolicy.startOption(positionMs: 1_010) == "start=1.010", "hundredth")
expect(PersonalNativeResumePolicy.startOption(positionMs: 1_100) == "start=1.100", "tenth")
expect(PersonalNativeResumePolicy.startOption(positionMs: 1_999) == "start=1.999", "fraction")
expect(PersonalNativeResumePolicy.startOption(positionMs: 1_800_125) == "start=1800.125", "film")
expect(PersonalNativeResumePolicy.startOption(positionMs: 86_400_000) == "start=86400.000", "limit")
expect(PersonalNativeResumePolicy.startOption(positionMs: 86_400_001) == nil, "above limit")
expect(PersonalNativeResumePolicy.startOption(positionMs: .max) == nil, "overflow")
expect(PersonalNativeResumePolicy.startOption(positionMs: .min) == nil, "underflow")
let url = "https://example.invalid/film?x=a,b"
expect(PersonalNativeResumePolicy.loadArguments(url: url, positionMs: 0) == [url, "replace"], "ordinary load")
expect(PersonalNativeResumePolicy.loadArguments(url: url, positionMs: 3_500) == [url, "replace", "-1", "start=3.500"], "separate URL argument")
expect(PersonalNativeResumePolicy.loadArguments(url: url, positionMs: 500) == [url, "replace"], "small resume fallback")
expect(PersonalNativeResumePolicy.loadArguments(url: url, positionMs: .max) == [url, "replace"], "invalid resume fallback")
print("PASS: native resume policy \(checks) assertions")
