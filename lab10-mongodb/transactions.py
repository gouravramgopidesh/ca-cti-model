"""Explicit whole-transaction retry and separate commit retry."""
import time
from pymongo.errors import PyMongoError
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

class InsufficientFunds(Exception): pass
class OutOfStock(Exception): pass
class InjectedFailure(Exception): pass


def transact(client, body, retries=5, journal=True, events=None):
    """At most one initial attempt + retries; never replay an ambiguous commit."""
    events = [] if events is None else events
    for attempt in range(retries + 1):
        with client.start_session() as session:
            session.start_transaction(read_concern=ReadConcern('snapshot'),
                                      write_concern=WriteConcern(w='majority', j=journal, wtimeout=10000))
            uncertain_commit = False
            try:
                result = body(session, attempt)
                for commit_attempt in range(6):
                    try:
                        session.commit_transaction()
                        return result
                    except PyMongoError as exc:
                        if not exc.has_error_label('UnknownTransactionCommitResult'):
                            if uncertain_commit:
                                raise RuntimeError('Commit outcome requires inspection; not replaying transaction') from exc
                            raise
                        uncertain_commit = True
                        events.append({'kind':'commit-retry','attempt':commit_attempt+1,'error':str(exc)})
                        if commit_attempt == 5:
                            # Do not retry the body when the commit outcome is unknown.
                            raise RuntimeError('Commit outcome unknown; inspect operation ID before retrying') from exc
                        time.sleep(0.1 * 2**commit_attempt)
            except Exception as exc:
                if session.in_transaction:
                    session.abort_transaction()
                if isinstance(exc, PyMongoError) and exc.has_error_label('TransientTransactionError') and attempt < retries:
                    delay = 0.1 * 2**attempt
                    events.append({'kind':'transaction-retry','attempt':attempt+1,'delay_s':delay,'code':getattr(exc,'code',None),'error':str(exc)})
                else:
                    raise
        time.sleep(delay)
    raise AssertionError('unreachable')
