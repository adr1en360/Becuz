import type { Investigation } from "@/lib/investigation";
import { Breakdown } from "./breakdown";
import { CauseList } from "./cause-list";
import { Convergence } from "./convergence";
import { Headline } from "./headline";
import { NextSteps } from "./next-steps";
import { RuledOut } from "./ruled-out";
import { RunDetails } from "./run-details";

export function Report({ data }: { data: Investigation }) {
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-4 pb-20 pt-8 sm:px-8 lg:pt-14">
      <div className="flex max-w-3xl flex-col gap-14">
      {data.status !== "complete" && (
        <section role="alert" className="rounded-2xl border border-accent px-5 py-4">
          <h2 className="font-semibold">This run is {data.status}.</h2>
          <ul className="mt-2 list-disc pl-5 text-muted">
            {data.errors?.map((error) => <li key={error}>{error}</li>)}
          </ul>
        </section>
      )}
      <Headline data={data} />
      <Breakdown tree={data.tree} />
      <CauseList causes={data.causes} />
      <RuledOut items={data.ruled_out} />
      <Convergence convergence={data.convergence} notTested={data.not_tested} />
      <NextSteps data={data} />
      <RunDetails data={data} />
      </div>
    </main>
  );
}
