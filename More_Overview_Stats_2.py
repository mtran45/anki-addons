# Modified from https://ankiweb.net/shared/info/531984586

import json
import os
import time
from aqt.overview import Overview


def overview_table(self):
    json_file = os.path.join(self.mw.pm.profileFolder(),
                             'More_Overview_Stats_2.json')

    if os.path.isfile(json_file):
        with open(json_file, mode='r') as f:
            settings = json.load(f)
    else:
        settings = {}

    current_deck_name = self.mw.col.decks.current()['name']

    correction_for_notes = 1
    last_match_length = 0

    if 'note_correction_factors' in settings:
        for fragment, factor in settings['note_correction_factors'].items():
            if current_deck_name.startswith(fragment):
                if len(fragment) > last_match_length:
                    correction_for_notes = int(factor)
                    last_match_length = len(fragment)

        # prevent division by zero and negative results
        if correction_for_notes <= 0:
            correction_for_notes = 1

    (total, mature, young, unseen, suspended, due, 
    prod, prod_mature, recog, recog_mature) = self.mw.col.db.first(
        u'''
          select
          -- total
          count(id),
          -- mature
          sum(case when queue = 2 and ivl >= 21
                   then 1 else 0 end),
          -- young / learning
          sum(case when queue in (1, 3) or (queue = 2 and ivl < 21)
                   then 1 else 0 end),
          -- unseen
          sum(case when queue = 0
                   then 1 else 0 end),
          -- suspended
          sum(case when queue < 0
                   then 1 else 0 end),
          -- due
          sum(case when queue = 1 and due <= ?
                   then 1 else 0 end),
          -- production         
          sum(case when queue in (-2,1,2,3) and ord = 0
                             then 1 else 0 end),
          -- production_mature                   
          sum(case when queue = 2 and ord = 0 and ivl >= 21
                             then 1 else 0 end),
          -- recognition
          sum(case when queue in (-2,1,2,3) and ord = 1
                             then 1 else 0 end),
          -- recognition_mature
          sum(case when queue = 2 and ord = 1 and ivl >= 21
                             then 1 else 0 end)
          from cards where did in {:s}
        '''.format(self.mw.col.sched._deckLimit()),
        round(time.time()))

    if not total:
        return u'<p>No cards found.</p>'

    scheduled_counts = list(self.mw.col.sched.counts())
    deck_is_finished = not sum(scheduled_counts)

    cards = {}

    cards['mature'] = mature / int(correction_for_notes)
    cards['young'] = young / int(correction_for_notes)
    cards['unseen'] = unseen / int(correction_for_notes)
    cards['suspended'] = suspended / int(correction_for_notes)

    cards['total'] = total / int(correction_for_notes)
    cards['learned'] = cards['mature'] + cards['young']
    cards['unlearned'] = cards['total'] - cards['learned']

    cards['new'] = scheduled_counts[0]
    cards['learning'] = scheduled_counts[1]
    cards['review'] = scheduled_counts[2]
    # cards['due'] = due + cards['review']

    cards['recog'] = recog
    cards['recog_mature'] = recog_mature

    cards['prod'] = prod
    cards['prod_mature'] = prod_mature

    cards_percent = {}

    cards_percent['mature'] = cards['mature'] * 1.0 / cards['total']
    cards_percent['young'] = cards['young'] * 1.0 / cards['total']
    cards_percent['unseen'] = cards['unseen'] * 1.0 / cards['total']
    cards_percent['suspended'] = cards['suspended'] * 1.0 / cards['total']

    cards_percent['total'] = 1.0
    cards_percent['learned'] = cards['learned'] * 1.0 / cards['total']
    cards_percent['unlearned'] = cards['unlearned'] * 1.0 / cards['total']

    cards_percent['new'] = cards['new'] * 1.0 / cards['total']
    cards_percent['learning'] = cards['learning'] * 1.0 / cards['total']
    cards_percent['review'] = cards['review'] * 1.0 / cards['total']
    # cards_percent['due'] = cards['due'] * 1.0 / cards['total']

    labels = {}

    labels['mature'] = _('Mature')
    labels['young'] = _('Young')
    labels['unseen'] = _('Unseen')
    labels['suspended'] = _('Suspended')

    labels['total'] = _('Total')
    labels['learned'] = _('Learned')
    labels['unlearned'] = _('Unlearned')

    labels['new'] = _('New')
    labels['learning'] = _('Learning')
    labels['review'] = _('Review')
    # labels['due'] = _('Due')

    labels['prod'] = _('Production')
    labels['recog'] = _('Recognition')

    for key in labels:
        labels[key] = u'{:s}:'.format(labels[key])

    button = self.mw.button

    output_table = u'''
      <style type="text/css">
      <!--
        hr {
            height: 1px;
            border: none;
            border-top: 1px solid #aaa;
        }

        td {
            vertical-align: top;
        }

        td.row1 {
            text-align: left;
        }

        td.row2 {
            text-align: right;
            padding-left: 1.2em;
            padding-right: 1.2em;
        }

        td.row3 {
            text-align: right;
        }

        td.new {
            font-weight: bold;
            color: #00a;
        }

        td.learning {
            font-weight: bold;
            color: #a00;
        }

        td.review {
            font-weight: bold;
            color: #080;
        }

        td.percent {
            font-weight: normal;
            color: #888;
        }

        td.mature {
            font-weight: normal;
            color: #008;
        }

        td.young {
            font-weight: normal;
            color: #008;
        }

        td.learned {
            font-weight: normal;
            color: #080;
        }

        td.unseen {
            font-weight: normal;
            color: #a00;
        }

        td.suspended {
            font-weight: normal;
            color: #a70;
        }

        td.total {
            font-weight: bold;
            color: #000;
        }
      -->
      </style>

      <table cellspacing="2">
    '''

    if not deck_is_finished:
        output_table += u'''
            <tr>
              <td class="row1">{label[new]:s}</td>
              <td class="row2 new">{cards[new]:d}</td>
              <td class="row3 percent">{percent[new]:.0%}</td>
            </tr>
            <tr>
              <td class="row1">{label[learning]:s}</td>
              <td class="row2 learning">{cards[learning]:d}</td>
              <td class="row3 percent">{percent[learning]:.0%}</td>
            </tr>
            <tr>
              <td class="row1">{label[review]:s}</td>
              <td class="row2 review">{cards[review]:d}</td>
              <td class="row3 percent">{percent[review]:.0%}</td>
            </tr>
            <tr>
              <td colspan="3"><hr /></td>
            </tr>
        '''.format(label=labels,
                   cards=cards,
                   percent=cards_percent)

    output_table += u'''
        <tr>
          <td class="row1">{label[mature]:s}</td>
          <td class="row2 mature">{cards[mature]:d}</td>
          <td class="row3 percent">{percent[mature]:.0%}</td>
        </tr>
        <tr>
          <td class="row1">{label[young]:s}</td>
          <td class="row2 young">{cards[young]:d}</td>
          <td class="row3 percent">{percent[young]:.0%}</td>
        </tr>
        <tr>
          <td colspan="3"><hr /></td>
        </tr>
        <tr>
          <td class="row1">{label[learned]:s}</td>
          <td class="row2 learned">{cards[learned]:d}</td>
          <td class="row3 percent">{percent[learned]:.0%}</td>
        </tr>
        <tr>
          <td class="row1">{label[unseen]:s}</td>
          <td class="row2 unseen">{cards[unseen]:d}</td>
          <td class="row3 percent">{percent[unseen]:.0%}</td>
        </tr>
        <tr>
          <td class="row1">{label[suspended]:s}</td>
          <td class="row2 suspended">{cards[suspended]:d}</td>
          <td class="row3 percent">{percent[suspended]:.0%}</td>
        </tr>
        <tr>
          <td colspan="3"><hr /></td>
        </tr>
        <tr>
          <td class="row1">{label[prod]:s}</td>
          <td class="row2 learned">{cards[prod]:d}</td>
          <td class="row3 mature">{cards[prod_mature]:d}</td>
        </tr>
        <tr>
          <td class="row1">{label[recog]:s}</td>
          <td class="row2 learned">{cards[recog]:d}</td>
          <td class="row3 mature">{cards[recog_mature]:d}</td>
        </tr>
        <tr>
          <td colspan="3"><hr /></td>
        </tr>
        <tr>
          <td class="row1">{label[total]:s}</td>
          <td class="row2 total">{cards[total]:d}</td>
          <td class="row3 percent">{percent[total]:.0%}</td>
        </tr>
    '''.format(label=labels,
               cards=cards,
               percent=cards_percent)

    output = ''

    if deck_is_finished:
        if (not 'options' in settings) or (settings['options'].get(
                'show_table_for_finished_decks', True)):
            output += output_table
            output += u'''
              </table>
              <hr style="margin: 1.5em 0; border-top: 1px dotted #888;" />
            '''

        output += u'''
          <div style="white-space: pre-wrap;">{:s}</div>
        '''.format(self.mw.col.sched.finishedMsg())
    else:
        output += output_table
        output += u'''
            <tr>
              <td colspan="3" style="text-align: center; padding-top: 0.6em;">{button:s}</td>
            </tr>
          </table>
        '''.format(button=button('study', _('Study Now'), id='study'))

    return output


# replace _table method
Overview._table = overview_table
