"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

type ManualTicketInput = {
  issue_description: string;
  type: string;
  queue: string;
};

type ManualTicketModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (ticketInput: ManualTicketInput) => void;
};

const TYPE_OPTIONS = [
  "Incident",
  "Major Incident",
  "Problem",
  "Security Incident",
  "Service Request",
] as const;

const QUEUE_OPTIONS = [
  "Site Reliability",
  "Core API",
  "Customer API",
  "IAM Platform",
  "Billing Operations",
  "Security Operations",
  "Database Reliability",
  "Release Engineering",
  "Messaging Platform",
  "Access Governance",
] as const;

export default function ManualTicketModal({
  open,
  onOpenChange,
  onSubmit,
}: ManualTicketModalProps) {
  const [referenceId, setReferenceId] = useState("");
  const [issueDescription, setIssueDescription] = useState("");
  const [incidentType, setIncidentType] = useState<string>(TYPE_OPTIONS[0]);
  const [queue, setQueue] = useState<string>(QUEUE_OPTIONS[0]);

  const canSubmit = useMemo(
    () => issueDescription.trim().length >= 5,
    [issueDescription]
  );

  useEffect(() => {
    if (!open) {
      setReferenceId("");
      setIssueDescription("");
      setIncidentType(TYPE_OPTIONS[0]);
      setQueue(QUEUE_OPTIONS[0]);
    }
  }, [open]);

  const handleSubmit = () => {
    if (!canSubmit) {
      return;
    }

    onSubmit({
      issue_description: issueDescription.trim(),
      type: incidentType,
      queue,
    });

    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-zinc-800 bg-zinc-950 text-zinc-100 sm:max-w-xl">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold tracking-tight">
            Create Manual Ticket
          </DialogTitle>
          <DialogDescription className="text-sm text-zinc-400">
            Submit a custom incident to run through the Ops Decision Engine analysis pipeline.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <div className="grid gap-2">
            <Label htmlFor="reference-id" className="text-zinc-300">
              Reference ID (optional)
            </Label>
            <Input
              id="reference-id"
              value={referenceId}
              onChange={(event) => setReferenceId(event.target.value)}
              placeholder="INC-XXXXX or external tracking ID"
              className="border-zinc-700 bg-zinc-900 text-zinc-100 placeholder:text-zinc-500"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="issue-description" className="text-zinc-300">
              Issue Description
            </Label>
            <Textarea
              id="issue-description"
              value={issueDescription}
              onChange={(event) => setIssueDescription(event.target.value)}
              placeholder="Describe the operational issue, impact, and any observed symptoms..."
              className="min-h-[120px] border-zinc-700 bg-zinc-900 text-zinc-100 placeholder:text-zinc-500"
            />
          </div>

          <div className="grid gap-2 sm:grid-cols-2 sm:gap-4">
            <div className="grid gap-2">
              <Label htmlFor="incident-type" className="text-zinc-300">
                Incident Type
              </Label>
              <Select value={incidentType} onValueChange={setIncidentType}>
                <SelectTrigger
                  id="incident-type"
                  className="border-zinc-700 bg-zinc-900 text-zinc-100"
                >
                  <SelectValue placeholder="Select incident type" />
                </SelectTrigger>
                <SelectContent className="border-zinc-700 bg-zinc-900 text-zinc-100">
                  {TYPE_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="queue" className="text-zinc-300">
                Queue
              </Label>
              <Select value={queue} onValueChange={setQueue}>
                <SelectTrigger id="queue" className="border-zinc-700 bg-zinc-900 text-zinc-100">
                  <SelectValue placeholder="Select queue" />
                </SelectTrigger>
                <SelectContent className="border-zinc-700 bg-zinc-900 text-zinc-100">
                  {QUEUE_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="bg-cyan-600 text-white hover:bg-cyan-500 disabled:bg-zinc-800 disabled:text-zinc-500"
          >
            Submit for Analysis
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
